# Notes to self on how to publish

1. Create feature branches from "dev" branch, either from issues or stand-alone
2. Create pull requests from feature branches to "dev" branch, perform review
3. Locally, run the following commands:
   - `git checkout dev`
   - `bumpver update --dry` or `bumpver update --tag-num --dry`
4. Take note of the generated new package version from the previous step
5. Update Change log section of main README and commit/push these changes to dev
6. Then run the following commands:

   - `bumpver update` or `bumpver update --tag-num`
   - `git push`
   - `git push --tags`

7. Got to [github](https://github.com/Firefly78/sila2-feature-lib)
8. Create a pull request from "dev" to "main" branch, name should be something like: `Merge v2025.34a0 into main`
9. Complete the merge request

10. Click "Create new release"
11. Choose the tag you just created.
12. Click "Generate release notes. Make sure it's somewhat correct - edit if needed
13. Click "Publish release"
