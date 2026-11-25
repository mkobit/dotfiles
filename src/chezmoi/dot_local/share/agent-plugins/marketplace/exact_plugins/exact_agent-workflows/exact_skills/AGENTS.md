# SBX task authority

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
