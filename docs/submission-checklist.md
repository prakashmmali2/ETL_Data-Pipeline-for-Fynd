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
- [ ] Review the 8-minute-59-second `docs/project-walkthrough.mp4` and confirm
  it accurately represents your project. The narration is locally synthesized
  and the slides are AI-assisted; edit or replace the draft if needed.
- [ ] Upload the reviewed video to YouTube as **Unlisted** and add its URL to
  the submission form. The video has not been uploaded and no YouTube URL is
  included in this repository.
- [ ] Submit through FyndHacks before your personal deadline and verify the
  page confirms that the submission was received.

## Suggested 8-minute walkthrough

1. **0:00-0:45 - Goal and scope:** Identify the SDET Intern practice project,
   explain that the records are synthetic, and state the assumptions.
2. **0:45-1:45 - Design:** Show the CSV input, validation/transform steps,
   rejects output, SQLite target, and release gate.
3. **1:45-3:00 - Data-quality behavior:** Explain invalid-row reasons,
   duplicate-SKU resolution, UTC normalization, and the row-accounting rule.
4. **3:00-5:15 - Tests:** Show representative positive, boundary, and negative
   tests, including the numeric release-gate checks.
5. **5:15-6:30 - Run and evidence:** Run the documented commands and show the
   passing test summary, JUnit report, and release-gate result.
6. **6:30-7:30 - Defects and limitations:** Explain the defect-log status and
   what is not covered, including production integrations and scale.
7. **7:30-8:00 - Close:** Summarize what you would adapt for the actual
   challenge prompt and point judges to the repository evidence.

Keep the video within 7-10 minutes, avoid showing secrets or personal data, and
test the unlisted link from a signed-out browser before sharing it.
