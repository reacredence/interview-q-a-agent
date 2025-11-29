# Interview Q&A Agent - Helm Chart

Helm chart for deploying the Interview Q&A Agent service (Deep Agent for generating interview questions).

## Structure

```
helm/
├── Chart.yaml                    # Chart metadata
├── templates/                     # Kubernetes manifests
│   ├── deployment.yml           # Deployment configuration
│   ├── service.yaml             # Service configuration
│   ├── ingress.yaml             # Ingress configuration
│   ├── configmap.yaml           # ConfigMap for non-sensitive config
│   ├── secret.yaml              # Secret for sensitive data
│   ├── hpa.yaml                 # Horizontal Pod Autoscaler
│   └── cronjob.yaml             # CronJob for daily batch runs
└── environments/                 # Environment-specific values
    ├── dev/
    │   └── values.yaml          # Development environment
    ├── prod/
    │   └── values.yaml          # Production environment
    └── test/
        └── values.yaml          # Test environment
```

## Required Secrets

The following secrets need to be configured in GitHub Actions:

### Development
- `OPENAI_API_KEY_DEV`
- `SERPAPI_API_KEY_DEV`
- `S3_ENDPOINT_URL_DEV`
- `S3_ACCESS_KEY_ID_DEV`
- `S3_SECRET_ACCESS_KEY_DEV`
- `S3_BUCKET_NAME_DEV`
- `S3_REGION_NAME_DEV`

### Production
- `OPENAI_API_KEY_PROD`
- `SERPAPI_API_KEY_PROD`
- `S3_ENDPOINT_URL_PROD`
- `S3_ACCESS_KEY_ID_PROD`
- `S3_SECRET_ACCESS_KEY_PROD`
- `S3_BUCKET_NAME_PROD`
- `S3_REGION_NAME_PROD`

## Required Variables

Configure these in GitHub repository variables:

### Development
- `DO_REGISTRY_URL_DEV` - e.g., `registry.digitalocean.com/cerebrone-dev/interview-q-a-agent-dev`
- `NAMESPACE_DEV` - e.g., `interview-q-a-agent`

### Production
- `DO_REGISTRY_URL_PROD` - e.g., `registry.digitalocean.com/cerebrone-dev/interview-q-a-agent-prod`
- `NAMESPACE_PROD` - e.g., `interview-q-a-agent`

## Deployment

### Manual Deployment (Development)

```bash
helm upgrade --install interview-q-a-agent helm/ \
  --set image.tag=abc123 \
  --set openaiApiKey=$OPENAI_API_KEY \
  --set serpapiApiKey=$SERPAPI_API_KEY \
  --set s3EndpointUrl=$S3_ENDPOINT_URL \
  --set s3AccessKeyId=$S3_ACCESS_KEY_ID \
  --set s3SecretAccessKey=$S3_SECRET_ACCESS_KEY \
  --set s3BucketName=$S3_BUCKET_NAME \
  --set s3RegionName=$S3_REGION_NAME \
  --namespace interview-q-a-agent \
  -f helm/environments/dev/values.yaml
```

### Manual Deployment (Production)

```bash
helm upgrade --install interview-q-a-agent helm/ \
  --set image.tag=abc123 \
  --set openaiApiKey=$OPENAI_API_KEY_PROD \
  --set serpapiApiKey=$SERPAPI_API_KEY_PROD \
  --set s3EndpointUrl=$S3_ENDPOINT_URL_PROD \
  --set s3AccessKeyId=$S3_ACCESS_KEY_ID_PROD \
  --set s3SecretAccessKey=$S3_SECRET_ACCESS_KEY_PROD \
  --set s3BucketName=$S3_BUCKET_NAME_PROD \
  --set s3RegionName=$S3_REGION_NAME_PROD \
  --namespace interview-q-a-agent \
  -f helm/environments/prod/values.yaml
```

## Domains

- **Development**: `interview-q-a-agent.dev.labcerebrone.com`
- **Production**: `interview-q-a-agent.prod.labcerebrone.com`
- **Test**: `interview-q-a-agent.test.labcerebrone.com`

## Resources

Default resource limits:
- CPU: 500m request, 1 limit
- Memory: 512Mi request, 1Gi limit

## CronJob

The CronJob runs daily at 09:00 UTC to generate interview questions in batch mode. It uses the same image as the deployment but runs `batch_runner.py` instead.

## Autoscaling

Autoscaling is disabled by default. To enable:

1. Set `autoscaling.enabled: true` in values.yaml
2. Configure min/max replicas and target CPU

## Notes

- The service requires OpenAI API key for question generation
- SerpAPI key is needed for research queries
- S3/DigitalOcean Spaces credentials are required for artifact storage
- All sensitive data is stored in Kubernetes secrets
- The CronJob runs batch processing daily at 09:00 UTC

