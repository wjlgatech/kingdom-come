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

`POST /outcomes`

Records a ministry outcome snapshot and returns an effectiveness band. SQLAlchemy model support lives in `backend.models.outcome.MinistryOutcome`.

## Orchestration

`POST /orchestration/actions`

Returns actionable class adjustments with group identifiers, reasons, and member counts.

## Web Workbench

`GET /`

Serves the public workbench UI from `frontend/`. The UI exercises the same JSON endpoints external integrations use.

## Verification

Run `python -m pytest` before shipping changes.
