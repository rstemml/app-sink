"""
Kubernetes operations and manifest management
"""

import logging
from typing import Dict, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from jinja2 import Template

from core.config import get_settings
from models.schemas import DeploymentCreate, DeploymentUpdate

logger = logging.getLogger(__name__)


class KubernetesManager:
    """Manages Kubernetes operations"""

    def __init__(self):
        settings = get_settings()
        try:
            # Load kubeconfig
            config.load_kube_config(config_file=settings.kubeconfig)
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.namespace_prefix = settings.namespace_prefix
            logger.info("Kubernetes client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def _get_namespace_name(self, app_name: str) -> str:
        """Generate namespace name for app"""
        return f"{self.namespace_prefix}{app_name}"

    def create_namespace(self, app_name: str) -> str:
        """Create namespace for app"""
        namespace_name = self._get_namespace_name(app_name)

        namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace_name,
                labels={"app": app_name, "managed-by": "app-sink"}
            )
        )

        try:
            self.core_v1.create_namespace(body=namespace)
            logger.info(f"Created namespace: {namespace_name}")
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Namespace already exists: {namespace_name}")
            else:
                raise

        return namespace_name

    def delete_namespace(self, app_name: str):
        """Delete namespace for app"""
        namespace_name = self._get_namespace_name(app_name)

        try:
            self.core_v1.delete_namespace(name=namespace_name)
            logger.info(f"Deleted namespace: {namespace_name}")
        except ApiException as e:
            if e.status != 404:  # Ignore not found
                raise

    def create_deployment(self, app_name: str, deployment_spec: DeploymentCreate) -> Dict:
        """Create Kubernetes deployment"""
        namespace = self._get_namespace_name(app_name)

        # Create namespace first
        self.create_namespace(app_name)

        # Parse resources
        resources = deployment_spec.resources.dict() if deployment_spec.resources else {}
        cpu_limit = resources.get("cpu", "500m")
        memory_limit = resources.get("memory", "512Mi")

        # Create container
        container = client.V1Container(
            name=app_name,
            image=deployment_spec.image,
            ports=[client.V1ContainerPort(container_port=deployment_spec.port)],
            env=[
                client.V1EnvVar(name=k, value=v)
                for k, v in (deployment_spec.env or {}).items()
            ],
            resources=client.V1ResourceRequirements(
                limits={"cpu": cpu_limit, "memory": memory_limit},
                requests={"cpu": cpu_limit, "memory": memory_limit}
            ),
            liveness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=deployment_spec.healthcheck.path if deployment_spec.healthcheck else "/health",
                    port=deployment_spec.port
                ),
                initial_delay_seconds=deployment_spec.healthcheck.initial_delay if deployment_spec.healthcheck else 10,
                period_seconds=deployment_spec.healthcheck.interval if deployment_spec.healthcheck else 30,
                timeout_seconds=deployment_spec.healthcheck.timeout if deployment_spec.healthcheck else 5
            ),
            readiness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=deployment_spec.healthcheck.path if deployment_spec.healthcheck else "/health",
                    port=deployment_spec.port
                ),
                initial_delay_seconds=5,
                period_seconds=10
            )
        )

        # Create deployment spec
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=app_name,
                namespace=namespace,
                labels={"app": app_name, "managed-by": "app-sink"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=deployment_spec.replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": app_name}
                    ),
                    spec=client.V1PodSpec(containers=[container])
                )
            )
        )

        try:
            result = self.apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Created deployment: {app_name}")
            return {"status": "created", "name": app_name}
        except ApiException as e:
            logger.error(f"Failed to create deployment: {e}")
            raise

    def create_service(self, app_name: str, port: int) -> Dict:
        """Create Kubernetes service"""
        namespace = self._get_namespace_name(app_name)

        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=app_name,
                namespace=namespace,
                labels={"app": app_name, "managed-by": "app-sink"}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": app_name},
                ports=[client.V1ServicePort(
                    port=80,
                    target_port=port,
                    protocol="TCP"
                )],
                type="ClusterIP"
            )
        )

        try:
            self.core_v1.create_namespaced_service(
                namespace=namespace,
                body=service
            )
            logger.info(f"Created service: {app_name}")
            return {"status": "created", "name": app_name}
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Service already exists: {app_name}")
            else:
                raise

    def create_ingress(self, app_name: str, domain: Optional[str] = None) -> Dict:
        """Create Kubernetes ingress with TLS"""
        if not domain:
            settings = get_settings()
            domain = f"{app_name}.{settings.default_domain}"

        namespace = self._get_namespace_name(app_name)

        ingress = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=app_name,
                namespace=namespace,
                labels={"app": app_name, "managed-by": "app-sink"},
                annotations={
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "traefik.ingress.kubernetes.io/router.entrypoints": "websecure"
                }
            ),
            spec=client.V1IngressSpec(
                ingress_class_name="traefik",
                tls=[client.V1IngressTLS(
                    hosts=[domain],
                    secret_name=f"{app_name}-tls"
                )],
                rules=[client.V1IngressRule(
                    host=domain,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="/",
                            path_type="Prefix",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=app_name,
                                    port=client.V1ServiceBackendPort(number=80)
                                )
                            )
                        )]
                    )
                )]
            )
        )

        try:
            self.networking_v1.create_namespaced_ingress(
                namespace=namespace,
                body=ingress
            )
            logger.info(f"Created ingress for {app_name}: {domain}")
            return {"status": "created", "domain": domain}
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Ingress already exists: {app_name}")
            else:
                raise

    def update_deployment(self, app_name: str, update_spec: DeploymentUpdate) -> Dict:
        """Update existing deployment"""
        namespace = self._get_namespace_name(app_name)

        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=app_name,
                namespace=namespace
            )

            # Update image if provided
            if update_spec.image:
                deployment.spec.template.spec.containers[0].image = update_spec.image

            # Update replicas if provided
            if update_spec.replicas is not None:
                deployment.spec.replicas = update_spec.replicas

            # Update env vars if provided
            if update_spec.env:
                deployment.spec.template.spec.containers[0].env = [
                    client.V1EnvVar(name=k, value=v)
                    for k, v in update_spec.env.items()
                ]

            # Update resources if provided
            if update_spec.resources:
                resources = update_spec.resources.dict()
                deployment.spec.template.spec.containers[0].resources = client.V1ResourceRequirements(
                    limits={
                        "cpu": resources.get("cpu", "500m"),
                        "memory": resources.get("memory", "512Mi")
                    }
                )

            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=app_name,
                namespace=namespace,
                body=deployment
            )

            logger.info(f"Updated deployment: {app_name}")
            return {"status": "updated", "name": app_name}

        except ApiException as e:
            logger.error(f"Failed to update deployment: {e}")
            raise

    def scale_deployment(self, app_name: str, replicas: int) -> Dict:
        """Scale deployment"""
        namespace = self._get_namespace_name(app_name)

        try:
            scale = client.V1Scale(
                metadata=client.V1ObjectMeta(name=app_name, namespace=namespace),
                spec=client.V1ScaleSpec(replicas=replicas)
            )

            self.apps_v1.patch_namespaced_deployment_scale(
                name=app_name,
                namespace=namespace,
                body=scale
            )

            logger.info(f"Scaled deployment {app_name} to {replicas} replicas")
            return {"status": "scaled", "replicas": replicas}

        except ApiException as e:
            logger.error(f"Failed to scale deployment: {e}")
            raise

    def delete_deployment(self, app_name: str) -> Dict:
        """Delete deployment and all related resources"""
        namespace = self._get_namespace_name(app_name)

        try:
            # Delete deployment
            self.apps_v1.delete_namespaced_deployment(
                name=app_name,
                namespace=namespace
            )

            # Delete service
            self.core_v1.delete_namespaced_service(
                name=app_name,
                namespace=namespace
            )

            # Delete ingress
            self.networking_v1.delete_namespaced_ingress(
                name=app_name,
                namespace=namespace
            )

            # Delete namespace (optional - contains all resources)
            # self.delete_namespace(app_name)

            logger.info(f"Deleted deployment: {app_name}")
            return {"status": "deleted", "name": app_name}

        except ApiException as e:
            if e.status != 404:  # Ignore not found
                logger.error(f"Failed to delete deployment: {e}")
                raise

    def get_deployment_status(self, app_name: str) -> Dict:
        """Get deployment status"""
        namespace = self._get_namespace_name(app_name)

        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=app_name,
                namespace=namespace
            )

            return {
                "name": app_name,
                "replicas": deployment.spec.replicas,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "status": "running" if deployment.status.ready_replicas == deployment.spec.replicas else "pending"
            }

        except ApiException as e:
            if e.status == 404:
                return {"name": app_name, "status": "not_found"}
            raise

    def get_logs(self, app_name: str, tail_lines: int = 100) -> str:
        """Get logs from deployment pods"""
        namespace = self._get_namespace_name(app_name)

        try:
            # Get pods for deployment
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={app_name}"
            )

            if not pods.items:
                return "No pods found"

            # Get logs from first pod
            pod_name = pods.items[0].metadata.name
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )

            return logs

        except ApiException as e:
            logger.error(f"Failed to get logs: {e}")
            raise

    def list_deployments(self) -> List[Dict]:
        """List all deployments managed by app-sink"""
        try:
            deployments = []
            namespaces = self.core_v1.list_namespace(
                label_selector="managed-by=app-sink"
            )

            for ns in namespaces.items:
                ns_deployments = self.apps_v1.list_namespaced_deployment(
                    namespace=ns.metadata.name
                )

                for dep in ns_deployments.items:
                    deployments.append({
                        "name": dep.metadata.name,
                        "namespace": dep.metadata.namespace,
                        "replicas": dep.spec.replicas,
                        "ready_replicas": dep.status.ready_replicas or 0,
                        "image": dep.spec.template.spec.containers[0].image,
                        "created_at": dep.metadata.creation_timestamp
                    })

            return deployments

        except ApiException as e:
            logger.error(f"Failed to list deployments: {e}")
            raise
