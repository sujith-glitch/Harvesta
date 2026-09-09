# Harvesta 3D Dashboard and Data Upgrade

## Goal

Improve the Harvesta dashboard with lightweight 3D-style motion and a trustworthy starter data package without breaking the existing farmer workflow or mobile performance.

## Approved design

### Visual layer

- Use CSS transforms, opacity, gradients, and existing icon assets for floating rings, gentle parallax, hover/tap lift, and animated status indicators.
- Do not add a heavy WebGL runtime for the dashboard.
- Respect `prefers-reduced-motion` and disable non-essential motion on small screens or when requested by the user.
- Keep all current navigation, cards, chat, and mobile bottom navigation intact.

### Data package

- Add versioned, documented starter data for disease classes/images metadata, sensor readings, weather history, soil/crop suitability, pest references, and fertilizer references.
- Prefer public/licensed sources and retain source, license, retrieval date, and field definitions in dataset manifests.
- Keep secrets and personal data out of datasets.
- Use small checked-in samples/manifests for development; avoid committing large raw archives.

### Model/backend integration

- Validate schemas and missing values before training.
- Retrain or benchmark existing disease and irrigation models only when the data meets the documented schema.
- Expose model metadata, source, version, and confidence in backend responses.
- Preserve safe prototype disclaimers and use deterministic fallback responses when a model or external provider is unavailable.

### Delivery stages

1. Add the visual layer and data manifests/sample loaders.
2. Add validation and benchmark/retraining scripts.
3. Connect validated artifacts to backend endpoints.
4. Run frontend/backend tests and mobile smoke checks.
5. Update deployment configuration and verify Render/Vercel integration.

## Acceptance criteria

- Dashboard has visible but subtle 3D-style motion and remains usable on phone.
- Reduced-motion users see no distracting animation.
- Dataset files include provenance and schema documentation.
- Existing tests pass; new validation tests cover malformed/missing data.
- Backend continues to start without external AI or sensor services.
