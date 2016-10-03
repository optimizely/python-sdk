#Contributing to the Optimizely Python SDK
We welcome contributions and feedback! All contributors must sign our [Contributor License Agreement (CLA)](https://docs.google.com/a/optimizely.com/forms/d/e/1FAIpQLSf9cbouWptIpMgukAKZZOIAhafvjFCV8hS00XJLWQnWDFtwtA/viewform) to be eligible to contribute. Please read the [README](README.md) to set up your development environment, then read the guidelines below for information on submitting your code.

##Development process

1. Create a branch off of `devel`: `git checkout -b YOUR_NAME/branch_name`.
2. Commit your changes. Make sure to add tests!
3. Lint your changes before submitting with `pep8 YOUR_CHANGED_FILES.py`.
4. `git push` your changes to GitHub.
5. Make sure that all unit tests are passing and that there are no merge conflicts between your branch and `devel`.
6. Open a pull request from `YOUR_NAME/branch_name` to `devel`.
7. A repository maintainer will review your pull request and, if all goes well, merge it!

##Pull request acceptance criteria

* **All code must have test coverage.** We use unittest. Changes in functionality should have accompanying unit tests. Bug fixes should have accompanying regression tests.
  * Tests are located in `/tests` with one file per class.
* Please don't change the `__version__`. We'll take care of bumping the version when we next release.
* Lint your code with PEP-8 before submitting.

##Style
We enforce PEP-8 rules with a few minor deviations.

##License

By contributing your code, you agree to license your contribution under the terms of the [Apache License v2.0](http://www.apache.org/licenses/LICENSE-2.0).

##Contact
If you have questions, please contact developers@optimizely.com.
