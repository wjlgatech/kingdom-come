# V7 Features

## Predictive
`POST /predictive/dropout-risk`

Scores student dropout risk from engagement and reflection signals. The response includes:

- `score`
- `level`
- `reasons`

## Adaptive
`POST /curriculum/recommendations`

Recommends curriculum from calling and previously completed content.

## Outcomes
`backend.models.outcome.MinistryOutcome`

SQLAlchemy model for ministry impact records. Database metadata is provided by `backend.db.connection`.

## Orchestration
`POST /orchestration/actions`

Returns actionable class adjustments with group identifiers, reasons, and member counts.

## Verification

Run `python -m pytest` before shipping changes.
