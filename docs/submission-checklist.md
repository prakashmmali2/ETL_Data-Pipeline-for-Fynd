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
- [ ] Review the 6-minute-53-second
  `docs/Project Overview Video.mp4` and confirm it accurately represents
  your project. The original Indian-English narration is preserved, with new
  animated visuals; review the draft before sharing.
- [ ] Upload the reviewed video to YouTube as **Unlisted** and add its URL to
  the submission form. The video has not been uploaded and no YouTube URL is
  included in this repository.
- [ ] Submit through FyndHacks before your personal deadline and verify the
  page confirms that the submission was received.

## Animated walkthrough sections

The narration and animated scenes follow these approximate section boundaries:

1. **0:00-0:50 - Goal and scope:** Identify the SDET Intern practice project
   and synthetic-data boundaries.
2. **0:50-1:34 - Source contract:** Explain the seven-column CSV schema.
3. **1:34-2:18 - Validation:** Show normalization, valid rows, and rejects.
4. **2:18-2:56 - Deduplication:** Show stable ordering and latest-update wins.
5. **2:56-3:36 - Loading:** Explain the SQLite upsert and constraints.
6. **3:36-4:17 - Accounting:** Reconcile rejected, duplicate, and loaded rows.
7. **4:17-4:52 - Quality gate:** Show the post-load checks.
8. **4:52-5:31 - Tests:** Cover contract, boundary, negative, and release tests.
9. **5:31-6:11 - Run evidence:** Show the sample counts and validation output.
10. **6:11-6:53 - Close:** State limitations and submission checks.

Keep the video within 7-10 minutes, avoid showing secrets or personal data, and
test the unlisted link from a signed-out browser before sharing it.
