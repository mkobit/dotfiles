# Agent skills

Reference: [Lessons from building Claude Code: How we use skills](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills)

1. **Library and API reference**
   These are skills that explain how to correctly use a library, CLI, or SDKs. They could be both for internal libraries or common libraries that Claude Code sometimes struggles to handle.

2. **Product verification**
   These are skills that describe how to test or verify that your code is working. They are often paired with playwright, tmux, or other external tools for verification.

3. **Data fetching and analysis**
   These are skills that connect to your data and monitoring stacks. These skills might include libraries to fetch your data with credentials, specific dashboard ids, etc., as well as instructions on common workflows or ways to get data.

4. **Business process and team automation**
   These are skills that automate repetitive workflows into one command. These skills are usually fairly simple instructions but might have more complicated dependencies on other skills or MCPs.

5. **Code scaffolding and templates**
   These are skills that generate framework boilerplates for a specific function in a codebase. You might combine these skills with scripts that can be composed.

6. **Code quality and review**
   These are skills that enforce code quality inside of your org and help review code. These can include deterministic scripts or tools for maximum robustness.

7. **CI/CD and deployment**
   These are skills that help you fetch, push, and deploy code inside of your codebase. These skills may reference other skills to collect data.

8. **Runbooks**
   These are skills that take a symptom (such as a Slack thread, alert, or error signature), walk through a multi-tool investigation, and produce a structured report.

9. **Infrastructure operations**
   These are skills that perform routine maintenance and operational procedures, some of which involve destructive actions that benefit from guardrails. These make it easier for engineers to follow best practices in critical operations.

## SBX task authority

Read the project instructions, latest-state records, and delegation rules before setup or task work.
Accept a complete task from a person or an agent.
Record its scope, branch and base, checks, authority, and return location.
The host coordinator owns Git delivery, signing, publishing, and tracker changes for a normal edit/check task.
An explicit private-clone task can assign these actions to the guest worker.
Apply that written assignment when a general host-only default differs.
Grant signing, remote writes, and tracker changes separately and only for the named task.
Do not infer authority from available credentials, tools, or a sandbox bypass flag.
Do not initialize a tracker as part of repository setup.

Keep direct-mounted defaults for tasks that use them.
Use a private clone when the task requires private Git and dependencies.
Each repository owns its complete kit, runtimes, tools, packages, network access, services, and checks.
Kit creation must install and trust the project tools and prepare frozen dependencies before task launch.
Do not require the person or worker to run manual tool or dependency setup.
Report a setup defect if creation does not leave the guest ready.
Keep native shared skills read-only and deploy repository skills through their source configuration.
The central command policy owns approvals.
Do not add command grants to the bootstrap or sandbox skill metadata.
