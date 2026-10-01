<p align="right">chalk ■</p>

<table width="100%" align="center">
  <tr>
    <th colspan="4" style="text-align:center;">Relevant Links</th>
  </tr>
  <tr>
    <td style="text-align:center;">
      <a href="">Chalk Dashboard</a>
    </td>
    <td style="text-align:center;">
      <a href="">Github Repo</a>
    </td>
    <td style="text-align:center;">
      <a href="https://docs.chalk.ai">Chalk Docs</a>
    </td>
    <td style="text-align:center;">
      <a href="https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ0Ji3tufAW6Cb114b7yV9sgIZqJ4BGpZxxsiXpve7VO6mR9v-enuf5_-UuwO3r5ILW9N3wxWY0M">FDE Office Hours</a>
    </td>
  </tr>
</table>

# Demo Chalk Sandbox
Build, deploy, and iterate faster with Chalk — a programmable feature engine that powers low-latency inference, rapid model iteration, and observability across your model lifecycle.

---

## Getting Started Developing in Chalk

To get up and running with Chalk, we'll:

1. Install the [chalk] CLI tool
2. (optional) Set up a virtual environment
3. Login to Chalk
4. Query your features
5. Deploy your features

## 1. Install Chalk

   Install the [Chalk command line tool](https://docs.chalk.ai/cli).
   The Chalk CLI allows you to create, update, and manage your feature
   pipelines directly from your terminal.

   > curl -s -L https://api.chalk.ai/install.sh | sh

## 2. (optional) Create and activate a virtual environment in your project directory

	Creating a virtual environment is a good practice to keep your project 
	dependencies isolated from your system dependencies.

	> python -m venv .venv 
	> source .venv/bin/activate

	Within your virtual environment you can install your dependencies using either 
	`pip install -r requirements.txt` or `uv sync` depending on your dependency manager. 

	If you happen to see an error on either syncing dependencies or during a deploy involving 
	`psycopg2`, then you will likely need to install Postgres: 

	> brew install postgres
    

## 3. Login or sign up

   Login or signup with Chalk directly from the command line. The
   [`chalk login`](https://docs.chalk.ai/cli/login) command will
   open your browser and create an API token for your local development.

## 4. Query your features

   Query your features directly from the command line with
   [`chalk query`](https://docs.chalk.ai/cli/query) to see that they're
   live and available.

_query for all the scalar features on the User feature class_

```sh
chalk query --in User.id=1
```

```python
from chalk.client import ChalkClient
from src.models import User

client = ChalkClient()

result = client.query(
    input={
        User.id: 1,
    },
    output=[
        User.name,
        User.email,
        User.risk_score,
        User.risk_category,
        User.txn_count,
        User.avg_txn_amount,
    ],
)
```

_query for some features of the Transaction feature class_

```sh
chalk query --in Transaction.id=1 --out Transaction.amount,Transaction.status,Transaction.processing_fee
```

```python
from chalk.client import ChalkClient
from src.models import Transaction

client = ChalkClient()

result = client.query(
    input={
        Transaction.id: 1,
    },
    output=[
        Transaction.amount,
        Transaction.status,
        Transaction.processing_fee,
    ],
)
```


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
      --in User.id=1
      --branch "$USER-branch"



---

## What is Chalk? - Brief Introduction
Build, deploy, and iterate faster with Chalk — a programmable feature engine that powers low-latency inference, rapid model iteration, and observability across your model lifecycle. [View the Chalk Docs!](https://docs.chalk.ai/docs/what-is-chalk)

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
chalk query --in User.id=1 --out User.risk_score,User.risk_category
```

When new features are created you can deploy your changes to the query server by running `chalk apply`.
If you run `chalk apply` directly, this will deploy your changes to the main deployment and rebuild the engine image.
However, for faster iteration during development, Chalk uses the concept of [branch deployments](https://docs.chalk.ai/docs/branches) which will run much faster:
```
chalk apply --branch <branch_name>
```
This allows for concurrent development similar to the functionality of git branches. If no name is given when running `chalk apply --branch` it will use your local git branch as the branch name.

## Assumptions

- Company name set to "Demo Chalk"
- `Transaction.at` is aliased as `created_at` in the SQL resolver for use in time-of-day expressions
- `CreditReport` is linked to `User` via a has-one relationship using `CreditReport.user_id`
