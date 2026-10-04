#!/usr/bin/env bash
# Deploy the daily_pipeline Cloud Function and (re)create its Cloud Scheduler job.
# Idempotent: safe to re-run after code changes. Run from the pipeline/ directory.
set -euo pipefail

PROJECT="training-performance-dashboard"
REGION="europe-west1"
FUNCTION="daily-pipeline"
RUNTIME_SA="pipeline-runner@${PROJECT}.iam.gserviceaccount.com"
INVOKER_SA="scheduler-invoker@${PROJECT}.iam.gserviceaccount.com"
# New projects no longer grant the default compute account build rights; use a dedicated one.
BUILD_SA="projects/${PROJECT}/serviceAccounts/function-builder@${PROJECT}.iam.gserviceaccount.com"
SCHEDULE="30 23 * * *"
TIME_ZONE="Europe/Istanbul"

gcloud functions deploy "$FUNCTION" \
  --project="$PROJECT" \
  --region="$REGION" \
  --gen2 \
  --runtime=python312 \
  --source=. \
  --entry-point=daily_pipeline \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account="$RUNTIME_SA" \
  --build-service-account="$BUILD_SA" \
  --memory=512Mi \
  --timeout=300s \
  --max-instances=1 \
  --quiet

URL=$(gcloud functions describe "$FUNCTION" --project="$PROJECT" --region="$REGION" \
  --format="value(serviceConfig.uri)")

gcloud functions add-invoker-policy-binding "$FUNCTION" \
  --project="$PROJECT" \
  --region="$REGION" \
  --member="serviceAccount:${INVOKER_SA}" \
  --quiet >/dev/null

scheduler_args=(
  --project="$PROJECT"
  --location="$REGION"
  --schedule="$SCHEDULE"
  --time-zone="$TIME_ZONE"
  --uri="$URL"
  --http-method=POST
  --oidc-service-account-email="$INVOKER_SA"
  --oidc-token-audience="$URL"
  --attempt-deadline=320s
)
if gcloud scheduler jobs describe "$FUNCTION" --project="$PROJECT" --location="$REGION" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "$FUNCTION" "${scheduler_args[@]}" --quiet
else
  gcloud scheduler jobs create http "$FUNCTION" "${scheduler_args[@]}" --quiet
fi

echo "Deployed ${FUNCTION}: ${URL} (schedule: ${SCHEDULE} ${TIME_ZONE})"
