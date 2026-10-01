<p align="right">chalk ■</p>

<table width="100%" align="center">
  <tr>
    <th colspan="3" style="text-align:center;">Relevant Links</th>
  </tr>
  <tr>
    <td style="text-align:center;">
      <a href="https://chalk.ai/environments/demo46428d94">Chalk Dashboard</a>
    </td>
    <td style="text-align:center;">
      <a href="https://github.com/chalk-ai/demo-chalk">Github Repo</a>
    </td>
    <td style="text-align:center;">
      <a href="https://docs.chalk.ai">Chalk Docs</a>
    </td>
  </tr>
</table>

# Demo Chalk Sandbox
Chalk is the platform for production AI. Define features, prompts, and models in
pure Python, serve them with low-latency online queries, build point-in-time
correct training sets with offline queries, and run agents and batch jobs in
sandboxes next to your data. Everything is versioned, branchable, and observable,
so you can go from notebook to production without rewriting your pipeline.

This repo is a small fraud-detection example you can deploy, query, and extend
to learn the core workflow.

---

## Table of Contents

- [Getting Started Developing in Chalk](#getting-started-developing-in-chalk)
- [Usage Examples](#usage-examples)
  - [Online Queries (CLI)](#online-queries-cli)
  - [Online Queries (Python)](#online-queries-python)
  - [Offline Queries (Python)](#offline-queries-python)
  - [Sandboxes (CLI)](#sandboxes-cli)
  - [Sandboxes (Python)](#sandboxes-python)
  - [Downloading Agent Skills](#downloading-agent-skills)
  - [Other Useful CLI Commands](#other-useful-cli-commands)
- [What is Chalk? - Brief Introduction](#what-is-chalk---brief-introduction)
- [Assumptions](#assumptions)

---

## Getting Started Developing in Chalk

To get up and running with Chalk, we'll:

1. Install the [chalk] CLI tool
2. Install dependencies with uv
3. Login to Chalk
4. Query your features
5. Deploy your features

## 1. Install Chalk

   Install the [Chalk command line tool](https://docs.chalk.ai/cli).
   The Chalk CLI allows you to create, update, and manage your feature
   pipelines directly from your terminal.

   > curl -s -L https://api.chalk.ai/install.sh | sh

## 2. Install dependencies with uv

   This project uses [uv](https://docs.astral.sh/uv/) to manage Python and its
   dependencies. Install it if you don't have it:

   > curl -LsSf https://astral.sh/uv/install.sh | sh

   Then, from the project root, create the virtual environment and install
   everything declared in `pyproject.toml` in one step:

   > uv sync

   This creates a `.venv/` with the pinned Python version and `chalkpy`, plus
   the dev tools (pytest, jupyter, and so on). You don't need to activate the
   environment to use it: prefix commands with `uv run`.

   > uv run python examples/online_query.py 1
   > uv run pytest tests/unit_tests.py

   If you prefer an activated shell, `source .venv/bin/activate` works as usual.

   If you see an error during `uv sync` or `chalk apply` involving `psycopg2`,
   install the Postgres client libraries:

   > brew install postgresql

## 3. Login or sign up

   Login or signup with Chalk directly from the command line. The
   [`chalk login`](https://docs.chalk.ai/cli/login) command will
   open your browser and create an API token for your local development.

## 4. Query your features

   Query your features directly from the command line with
   [`chalk query`](https://docs.chalk.ai/cli/query) to see that they're
   live and available.

```sh
chalk query --in user.id=1
```

   See [Usage Examples](#usage-examples) below for many more ways to query,
   both from the CLI and from Python.

## 5. Deploy your features

   Deploy your feature pipeline to production or to a branch. After
   you've written some new features and resolvers, use the [chalk apply --branch](https://docs.chalk.ai/cli/apply)
   command to deploy your feature pipelines.
  
   When testing new code, we recommend using a Chalk "branch".
   To deploy to a branch, just add **--branch <branch_name>** to your chalk
   command. To deploy your code to production (which provides dynamic horizontal
   scaling and zero downtime deployments) you'll use [chalk apply].
  
   To test branch deployments out, after pulling this repo run:
  
    chalk apply --branch "$USER-branch"
   
  
   which will deploy your local code to a branch called <your-username>-branch
  
   The code you just deployed can immediately be queried using the **--branch** flag
   For example:

    chalk query
      --in user.id=1
      --branch "$USER-branch"

---

## Usage Examples

The examples below all use the feature classes defined in [`src/models.py`](src/models.py):
`User`, `Transaction`, and `CreditReport`. Runnable versions of several of these
live in the [`examples/`](examples/) directory.

### Online Queries (CLI)

[Online queries](https://docs.chalk.ai/docs/query-basics) compute features for a
single entity with low latency. The CLI is the fastest way to check that a
feature resolves correctly.

On the CLI, feature names are the lowercase fully qualified names Chalk uses on
the wire: `user.id`, not `User.id`.

_Query every scalar feature on a `User`:_

```sh
chalk query --in user.id=1
```

_Query a specific set of output features:_

```sh
chalk query --in user.id=1 --out user.risk_score,user.risk_category
```

_Query across a has-one relationship (`User` → `CreditReport`):_

```sh
chalk query --in user.id=1 \
  --out user.name \
  --out user.credit_report.score \
  --out user.credit_report.percent_past_due
```

_Query has-many aggregates and a windowed feature. Requesting the windowed
feature by name returns every window; to pick one window, use the duration in
seconds (`7d` = `604800`):_

```sh
chalk query --in user.id=1 \
  --out user.txn_count \
  --out user.avg_txn_amount \
  --out user.recent_spending

chalk query --in user.id=1 \
  --out user.recent_spending__604800__ \
  --out user.recent_spending__2592000__
```

_Query the other side of the join, from a `Transaction`:_

```sh
chalk query --in transaction.id=1 \
  --out transaction.amount,transaction.status,transaction.processing_fee,transaction.is_night
```

_Query against a branch deployment instead of the main deployment:_

```sh
chalk query --in user.id=1 --out user.risk_category --branch "$USER-branch"
```

_Explain how the planner will execute a query without running resolvers:_

```sh
chalk query --in user.id=1 --out user.ach_return_ratio --explain
```

_Get machine-readable output for scripting:_

```sh
chalk query --in user.id=1 --out user.risk_score --json
```

Each query prints a link to the Chalk Dashboard showing exactly how the query
was executed, which resolvers ran, and how long each step took.

### Online Queries (Python)

The [`ChalkClient`](https://docs.chalk.ai/api-docs#ChalkClient) picks up
credentials from `chalk login` locally, or from the `CHALK_CLIENT_ID` /
`CHALK_CLIENT_SECRET` environment variables in production.

_Basic query using feature class references:_

```python
from chalk.client import ChalkClient
from src.models import User

client = ChalkClient()

result = client.query(
    input={User.id: 1},
    output=[
        User.name,
        User.email,
        User.risk_score,
        User.risk_category,
        User.txn_count,
        User.avg_txn_amount,
    ],
)

print(result.get_feature_value(User.risk_score))
```

_Same query using string feature names (no `src` import required, useful from
other services or inside a sandbox):_

```python
from chalk.client import ChalkClient

client = ChalkClient()

result = client.query(
    input={"user.id": 1},
    output=[
        "user.name",
        "user.risk_score",
        "user.risk_category",
        "user.credit_report.score",
    ],
)

for feat in result.data:
    print(f"{feat.field}: {feat.value}")
```

A runnable version of this is in [`examples/online_query.py`](examples/online_query.py):

```sh
uv run examples/online_query.py 1
```

_Query against a branch:_

```python
client = ChalkClient(branch="my-branch")
result = client.query(input={User.id: 1}, output=[User.risk_category])
```

_Query many entities at once with `query_bulk`:_

```python
result = client.query_bulk(
    input={User.id: [1, 2, 3, 4, 5]},
    output=[User.risk_score, User.risk_category, User.ach_return_ratio],
)

print(result)
```

_Request a has-many DataFrame as an output:_

```python
from chalk.features import DataFrame
from src.models import Transaction

result = client.query(
    input={User.id: 1},
    output=[User.transactions[Transaction.amount, Transaction.merchant, Transaction.status]],
)

txns: DataFrame = result.get_feature_value(User.transactions)
print(txns)
```

_Attach a query name for observability, and set a max staleness to prefer
cached values from the online store:_

```python
result = client.query(
    input={User.id: 1},
    output=[User.risk_score],
    query_name="fraud_risk_check",
    staleness={User.risk_score: "1h"},
)
```

### Offline Queries (Python)

[Offline queries](https://docs.chalk.ai/docs/query-offline) compute features
for many entities as of specific points in time. They are the primary way to
build point-in-time correct training datasets. Offline queries return a
`Dataset` that you can pull into pandas, polars, or Arrow.

_Build a training set for a list of users as of now:_

```python
from chalk.client import ChalkClient
from src.models import User

client = ChalkClient()

dataset = client.offline_query(
    input={User.id: list(range(1, 1001))},
    output=[
        User.risk_score,
        User.txn_count,
        User.avg_txn_amount,
        User.night_txn_ratio,
        User.ach_return_ratio,
        User.credit_report.score,
        User.is_fraud,  # label
    ],
    recompute_features=True
    dataset_name="fraud_training_v1",
)

df = dataset.to_polars()
print(df.head())
```

_Point-in-time correct features using `input_times`. Each feature value is
computed as it would have been observed at that timestamp, so no label
leakage from the future:_

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
user_ids = [1, 2, 3, 4, 5]
observed_at = [now - timedelta(days=i * 7) for i in range(len(user_ids))]

dataset = client.offline_query(
    input={User.id: user_ids},
    input_times=observed_at,
    output=[
        User.recent_spending["7d"],
        User.recent_spending["30d"],
        User.txn_count,
        User.is_fraud,
    ],
    recompute_features=True,
    dataset_name="fraud_training_pit",
)

df = dataset.to_polars()
```

Datasets are also visible in the Chalk Dashboard and from the CLI with
`chalk dataset list`.

### Sandboxes (CLI)

[Sandboxes](https://docs.chalk.ai/docs/sandboxes) are long-lived containers
running inside your Chalk environment. They are useful for interactive
development, debugging, running scripts next to your data, and running agents
with access to Chalk features and secrets. A sandbox stays up until you
terminate it or its `--lifetime` expires.

_One-shot: upload a script, run it, and clean up afterwards:_

```sh
chalk sandbox create -i python:3.12 --rm \
  --with-local-file ./examples/online_query.py:/app/online_query.py \
  --chalk-identity \
  --exec bash -- -c "pip install -q 'chalkpy[all]' && python /app/online_query.py 1"
```

`--chalk-identity` injects Chalk workload credentials, so `ChalkClient()`
authenticates inside the sandbox without any extra config. `--rm` terminates
the sandbox when the command exits.

_Interactive shell that terminates on exit:_

```sh
chalk sandbox create -i python:3.12 --rm --exec-tty -- bash
```

_Leave a named sandbox running for the day, then exec into it as needed:_

```sh
chalk sandbox create -i python:3.12 -n dev-box --lifetime 8h --chalk-identity

chalk sandbox exec -n dev-box -- pip install 'chalkpy[all]'
chalk sandbox exec -n dev-box -- python -c "from chalk.client import ChalkClient; print(ChalkClient().query(input={'user.id': 1}, output=['user.risk_score']).data)"
chalk sandbox exec -n dev-box -t -- bash   # interactive shell
```

_Inject secrets stored in Chalk, or create one from your local environment:_

```sh
chalk sandbox create -i python:3.12 -n agent-box --lifetime 2h \
  --chalk-identity \
  --secret-from-chalk CHALK_ROUTER_API_KEY \
  --secret-from-local-env OPENAI_API_KEY
```

_Restrict network egress and size the container for the job:_

```sh
chalk sandbox create -i python:3.12 --rm \
  --cpu 2 --memory 4Gi \
  --route '10.0.0.0/8=443,5432' \
  --with-local-file ./train.py:/app/train.py \
  --exec python -- /app/train.py
```

_Mount a Chalk volume (for example, a dataset you exported):_

```sh
chalk sandbox create -i python:3.12 --rm \
  --volume chalk://fraud-training-v1 \
  --exec ls -- /mnt/fraud-training-v1
```

_Manage running sandboxes:_

```sh
chalk sandbox list
chalk sandbox get -n dev-box
chalk sandbox terminate -n dev-box
```

### Sandboxes (Python)

The [`chalkcompute`](https://pypi.org/project/chalkcompute/) package exposes
the same sandbox primitives from Python, which is convenient for orchestrating
agents or batch jobs programmatically.

_Define an image, run a script in a sandbox, and tear it down:_

```python
import uuid
from pathlib import Path

from chalkcompute import Image, NetworkPolicy, Sandbox, Secret

image = (
    Image.debian_slim("3.12")
    .pip_install(["chalkpy[all]"])
    .add_local_file("examples/online_query.py", "/app/online_query.py")
    .workdir("/app")
)

sandbox = Sandbox(
    image=image,
    name=f"query-{uuid.uuid4().hex[:8]}",
    chalk_identity=True,
    network_policy=NetworkPolicy(allowed_hosts=["*.chalk.ai"]),
    cpu="1",
    memory="2Gi",
).run()

try:
    result = sandbox.exec("python", "online_query.py", "1", timeout_secs=120)
    print(result.stdout_text)
finally:
    sandbox.terminate()
```

### Downloading Agent Skills

Chalk publishes reusable instruction skills for coding agents (Claude Code,
Codex, and Cursor) from the
[`chalk-ai/agent-prompts`](https://github.com/chalk-ai/agent-prompts)
repository. Installing them teaches your agent Chalk-specific patterns so it
writes correct resolvers, expressions, and notebooks on the first try.

Available skills:

| Skill | Use it when |
| --- | --- |
| `chalk-notebooks` | Exploring features and running queries from Jupyter |
| `writing-online-resolvers` | Writing or debugging `@online` Python resolvers |
| `writing-static-chalkdf` | Writing `@online(static=True)` resolvers with `chalkdf` |
| `chalk-resolver-acceleration` | Deciding whether to move resolver logic into `F.*` / `_` expressions |
| `chalk-streaming` | Writing Kafka, Kinesis, or PubSub stream resolvers |
| `migrating-features-to-chalk` | Porting dbt, Spark, pandas, or feature store pipelines into Chalk |

_Install a skill into this project for Claude Code (lands in `.claude/skills/`):_

```sh
chalk install agent-skill chalk-notebooks --claude
```

_Install several skills for multiple agents at once:_

```sh
chalk install agent-skill chalk-notebooks writing-online-resolvers writing-static-chalkdf \
  --claude --codex --cursor
```

_Install globally so every project on your machine gets them:_

```sh
chalk install agent-skill chalk-notebooks writing-online-resolvers --claude --global
```

_Install into a custom skills directory:_

```sh
chalk install agent-skill chalk-streaming --path ./agent-skills
```

_Update skills (re-running the command refreshes changed files) or remove one:_

```sh
chalk install agent-skill chalk-notebooks --claude           # update
chalk install agent-skill chalk-notebooks --claude --delete  # remove
```

Chalk also ships an MCP server for coding agents. See `chalk mcp --help` to
wire it up alongside the skills.

### Other Useful CLI Commands

Beyond `query` and `apply`, the CLI covers most of the day-to-day workflow.
Every command accepts `--environment <name>` and `--branch <name>` to target a
specific environment or branch, and `--json` for machine-readable output.
Run `chalk <command> --help` for full details on any of them.

#### Setup and authentication

```sh
chalk login                        # open a browser and create a local API token
chalk update                       # upgrade the CLI (old build kept in ~/.chalk/bin/)
chalk ping                         # check connectivity to the API and query servers
chalk project                      # print project info from chalk.yaml
chalk project --edit               # open chalk.yaml in your editor
```

_Inspect the credentials the CLI is using, or export them for other tools:_

```sh
chalk config                       # table of client id, secret, env, API hosts
chalk config --format env          # KEY=VALUE lines, ready for a .env file
chalk config --format shell        # export statements: eval "$(chalk config --format shell)"
chalk config --format chalkpy      # a ready-to-paste ChalkClient(...) constructor
```

#### Validating and deploying

_Lint before you deploy. Local-only linting needs no network:_

```sh
chalk lint                         # local + remote validation
chalk lint --local                 # local validation only
```

_Preview a deploy without executing it:_

```sh
chalk apply --plan                 # show the feature/resolver diff and stop
chalk apply --dump                 # print the generated apply payload for debugging
```

_Deploy to a branch and keep it in sync as you edit:_

```sh
chalk apply --branch "$USER-branch"           # ~5s branch deploy
chalk apply --branch "$USER-branch" --watch   # re-apply on every file save
chalk apply --branch "$USER-branch" --reset   # discard notebook edits, deploy working dir as-is
```

#### Datasets

Offline queries produce datasets. You can list, inspect, download, and upload
them from the CLI.

```sh
chalk dataset list                                   # most recent 50 datasets
chalk dataset list --search fraud_training           # filter by name
chalk dataset get <dataset-id>                       # details and revisions
chalk dataset download <revision-id> --output-dir ./data
chalk dataset download <revision-id> --include-givens --include-traces
chalk dataset upload ./labels.parquet --name fraud_labels_2024
chalk dataset rename <dataset-id> fraud_training_v2
chalk dataset archive <revision-id>
```

---

## What is Chalk? - Brief Introduction
Chalk is the platform for production AI: a programmable feature engine that powers low-latency inference, point-in-time correct training data, rapid model iteration, and observability across your model lifecycle. [View the Chalk Docs!](https://docs.chalk.ai/docs/what-is-chalk)

There are four core concepts to development in Chalk:
1. Data Sources
   * Connecting in Chalk Dashboard
   * Referencing in Python
2. Defining Features 
    * Feature Classes
    * Joins
3. Creating Resolvers
   * SQL Resolvers
    * Chalk Expressions
    * Python Resolvers
4. Running Queries and Deploying Changes
   * Running Queries
   * Main Deployment 
   * Branch Deployment
   
### 1. Data Sources
Chalk is able to integrate directly with [many different data sources](https://docs.chalk.ai/docs/integrations). Adding data source integrations is done on the Chalk Dashboard. Once created on the Dashboard, data sources can be referenced in Python by defining:
```
from chalk.sql import PostgreSQLSource

pg = PostgreSQLSource(name="pg")
```
Where `name="pg"` matches the name given to this data source in the Dashboard. 

### 2. Features
In Chalk, features are defined in feature classes, which are just python classes that have the `@features` decorator.
Often, it is useful to think of feature classes as tables of features. The example below shows a feature class called `User`, which contains fraud-related features. 
```
@features
class User:
    id: int                   # Primary Key
    email: str
    name: str
    risk_score: float
    transactions: DataFrame[Transaction]
```
Defining feature classes allows us to define joins between classes.
We can do this by defining a join condition:
```
@features
class Transaction:
    id: int
    user_id: "User.id"
    amount: float
```
Using this syntax, each user has many transactions and each transaction belongs to one user.

Additional Documentation on Features and Joins:
- [Features Types](https://docs.chalk.ai/docs/feature-types)
- [DataFrames](https://docs.chalk.ai/docs/dataframe)
- [has_one](https://docs.chalk.ai/docs/has-one)
- [has_many](https://docs.chalk.ai/docs/has-many)

### 3. Resolvers
Chalk is a feature engine, and resolvers are components of code that tell the engine how to compute features. All resolvers can be thought of as building blocks for queries that define how to get from `Feature Set A` → `Feature Set B`.

#### SQL Resolvers
The first type of resolver is a SQL Resolver. These are SQL files that end in the suffix `.chalk.sql` and they contain comments in the header followed by a SQL query.
The comments in the header of the script tells Chalk where to run this query and what feature class is resolved:
```
-- source: pg
-- resolves: User

SELECT
    id,
    email,
    name,
    risk_score
FROM users
```
In this example, `pg` is the Postgres Database that we connected in the Chalk Dashboard, and `User` is the feature class that is resolved. 

#### Chalk Expressions

Expressions are inline feature definitions that are ultra-fast and run directly in the execution plan.
Chalk supports most built-in python functions and hundreds of [Chalk Functions](https://docs.chalk.ai/api-docs#section-chalk-functions). 
Chalk expressions can be defined using the `_` syntax, which allows for reference to the parent class:
```
@features
class Transaction:
    id: int                   
    amount: float
    is_small: bool = _.amount < 5.0
```
You can also defined windowed aggregates directly in Chalk using `Windowed` features:
```
@features
class User:
    id: int
    transactions: DataFrame[Transaction]
    recent_spending: Windowed[float] = windowed(
        "1d", "7d", "30d",
        expression=_.transactions[
            _.amount,
            _.created_at > _.chalk_window,
            _.created_at < _.chalk_now,
        ].sum(),
    )
```


#### Python Resolvers

Resolvers can also be written directly in python. To define a python resolver, you decorate a python function with `@online`, `@offline`, or `@stream` depending on when you want this resolver to run. Online queries are meant to run with low latency in realtime, while offline queries are meant to run in batch cases where additional latency is acceptable. In the query engine, resolvers marked with `@online` can be used in any query where as those marked in `@offline` will not be used for online queries.      

Python resolvers can contain complex logic, make API calls, and call python libraries. The engine will decide when to use a python resolver based on the input and output features.
```
@online
def get_email_domain(email: User.email) -> User.email_domain:
    return email.split("@")[-1].lower()
```

Chalk will parse the Abstract Syntax Tree of a python resolver and accelerate it by converting it to C++.

Additional Documentation on Resolvers:
- [Resolvers](https://docs.chalk.ai/docs/resolver-overview)
- [Online/Offline](https://docs.chalk.ai/docs/resolver-online-offline)
- [SQL Resolvers](https://docs.chalk.ai/docs/sql-resolvers)
- [Expressions](https://docs.chalk.ai/docs/expression)
- [Python Resolvers](https://docs.chalk.ai/docs/python-resolvers)


### 4. Running Queries and Deploying Changes
Chalk provides two main ways of accessing your features, the [CLI](https://docs.chalk.ai/cli) and the [Chalk Client](https://docs.chalk.ai/docs/query-basics). Queries run passing in an input feature, such as the primary key, and asking for a set of output features. 
```
chalk query --in user.id=1 --out user.risk_score,user.risk_category
```

When new features are created you can deploy your changes to the query server by running `chalk apply`.
If you run `chalk apply` directly, this will deploy your changes to the main deployment and rebuild the engine image.
However, for faster iteration during development, Chalk uses the concept of [branch deployments](https://docs.chalk.ai/docs/branches) which will run much faster:
```
chalk apply --branch <branch_name>
```
This allows for concurrent development similar to the functionality of git branches. If no name is given when running `chalk apply --branch` it will use your local git branch as the branch name.
