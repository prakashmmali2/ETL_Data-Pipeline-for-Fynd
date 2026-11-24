# SDET Intern submission checklist

This project is a practice ETL test harness. The actual challenge use case is
provided after registration, so compare this project with that prompt and adapt
it before submitting. Do not present this repository as an official Fynd
integration or as a completed FyndHacks submission.

## Prepare the submission

- [ ] Read the use case for your selected track and work individually within
  the supplied challenge rules and your personal 24-hour window. Keep
  challenge materials private and use only the supplied sandbox.
- [ ] Submit either the repository link or a code ZIP. The current repository
  link is <https://github.com/prakashmmali2/ETL_Data-Pipeline-for-Fynd>.
- [ ] Verify the chosen link opens for the judges (for a private repository,
  grant the required access; for a ZIP, include the project files and docs).
- [ ] Follow the exact setup and run steps in the repository README.
- [ ] Include the automated test results at
  `test-results/pytest-results.xml` and the test summary in
  `docs/validation-results.md`.
- [ ] Include `docs/defect-log-template.md`. It records that no application
  defects were observed in the documented validation; update it with
  reproducible findings if further testing discovers any.
- [ ] State assumptions, known gaps, and untested areas from
  `docs/test-plan.md`. Do not claim this local harness was tested against
  Fynd systems or the private challenge prompt.
- [ ] Use only synthetic or challenge-provided data. Check that the repository,
  ZIP, reports, and video contain no credentials, personal data, or
  proprietary material.
- [ ] Review the 7-8 minute
  `docs/Project Overview Video.mp4` and confirm it accurately represents
  your project. It uses a male Indian-English neural voice in the requested
  style and newly animated visuals; the original source video is retained,
  but its embedded narration is not reused.
- [ ] Upload the reviewed video to YouTube as **Unlisted** and add its URL to
  the submission form. The video has not been uploaded and no YouTube URL is
  included in this repository.
- [ ] Submit through FyndHacks before your personal deadline and verify the
  page confirms that the submission was received.

## Animated walkthrough sections

The video moves through nine animated scenes in this order:

1. Overall project scope: the shop and data pipeline.
2. The six-product storefront and cart interactions.
3. Checkout validation and fixed-price handling.
4. Local order API, CSV persistence, ETL, SQLite, and confirmation details.
5. ETL extraction, schema contract, transformations, and rejects.
6. Composite `(order_id, sku)` identity and safe upserts.
7. Row accounting and the release quality gate.
8. ETL and browser test evidence.
9. End-to-end recap and honest project boundaries.

The rendered runtime is 7:39, within the generator's enforced 7-8 minute
target. Avoid showing secrets or personal data, and test the unlisted link from
a signed-out browser before sharing it.
