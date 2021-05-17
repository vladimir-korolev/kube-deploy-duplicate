from eks_token import get_token
from datetime import datetime
import boto3


class KubeEKSClusterInfo:
    """
    Object with information about Kubernetes cluster. This instance is intended for EKS. It can be replaced with another one for another type of cluster
    :param cluster_name: It's a cluster name for AWS EKS
    :param eks_region: (optional) region name for AWS EKS
    :param time_lag: (optional) time before token has expired
    Public methods:
        - getSessionToke() : returns kubernetes session authorisation token
        - getEndpoint() : returns kubernetes API endpoint
        - isTokenExpired(): returns True if token was expired or expires in time_lag seconds
    """

    def __init__(self, cluster_name, eks_region='us-east-1', time_lag=60):
        self._cluster_name = cluster_name
        self._eks_region = eks_region
        self._time_lag = time_lag
        self._endpoint = self.getEndpoint()
        self._refreshSessionToken()


    def getSessionToken(self):
        if self.isTokenExpired():
            self._refreshSessionToken()
        return self._session_token['status']['token']

    def isTokenExpired(self):
        return (self._getSessionTokenExpirationTime() - datetime.utcnow()).total_seconds() < self._time_lag

    def getAuthorizationType(self) -> str:
        return 'Bearer'

    def getEndpoint(self):
        try:
            return \
                boto3.client('eks', region_name=self._eks_region).describe_cluster(name=self._cluster_name)['cluster']['endpoint']
        except Exception as e:
            print(e)

    def _refreshSessionToken(self):
        self._session_token = get_token(self._cluster_name)
        return self._session_token

    def _getSessionTokenExpirationTime(self):
        return datetime.strptime(self._session_token['status']['expirationTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

    def _getCurrentSessionToken(self):
        return self._session_token['status']['token']
