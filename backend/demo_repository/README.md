# ForgeOS Demo Repository

Small FastAPI service used by ForgeOS for reliable live demos.

The project intentionally starts with two test failures:

- `GET /items/{id}` returns `null` for missing items instead of a 404.
- `User` is missing an `is_valid()` method used by the model tests.

ForgeOS should copy this repository into a temporary workspace, run pytest,
classify the failures, patch the source files, and verify the tests pass.

