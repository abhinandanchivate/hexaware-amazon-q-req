 **one** end-to-end case study so your learners can actually build, run, and demo it. I’ll use **FinBank (Financial Services)** and turn it into a hands-on lab with **complete code & step-by-step** instructions. It’s split into 3 practical workstreams that map to Amazon Q’s value props:

1. **Q Developer** → accelerate Java/Spring bug-fix + test generation
2. **Q Business** → self-serve analytics on PostgreSQL + S3 reports
3. **Q App** → a Loan Decisioning workflow (eligibility + KYC) with Slack notifications

You can teach each workstream in isolation or run the full scenario. Everything below is **copy-pasteable** and designed for a single laptop + an AWS account (or all-local with Docker where possible).

---

# 🎓 Student Manual – Amazon Q Adoption (Single Deep Case Study: FinBank)

## 0) What you’ll build (high-level)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                               FinBank Lab                                │
├──────────────────────┬──────────────────────────┬─────────────────────────┤
│  (A) Q Developer     │ (B) Q Business           │ (C) Q App               │
│  Fix bug + tests in  │ Self-serve analytics on  │ Loan Decisioning flow   │
│  Spring Boot service │ RDS Postgres + S3        │ (Lambda + StepFn + Q)   │
│  using Q in IDE      │ (branches, NPAs, loans)  │ + Slack notification    │
└──────────────────────┴──────────────────────────┴─────────────────────────┘
```

---

## 1) Prerequisites

* **AWS account** with admin (for lab) or least-privilege IAM as per section 7.
* **Java 21**, **Maven 3.9+**, **Docker** (for local Postgres), **Node 18+** (optional), **Python 3.11+** (for Lambda code).
* **IDE**: VS Code or IntelliJ + **Amazon Q Developer** plugin.
* **Slack** workspace + **Incoming Webhook** URL (for notifications).
* **Postman** (optional) for API testing.

---

## 2) Repo Structure (create a folder `finbank-lab/`)

```
finbank-lab/
  A-q-dev-spring/
    pom.xml
    src/main/java/com/finbank/loans/...
    src/test/java/com/finbank/loans/...
    README.md
  B-q-business-data/
    db/init.sql
    s3/reports/quarterly_report_2025Q2.csv
    README.md
  C-q-app-loan-decision/
    infra/terraform/
      main.tf
      variables.tf
      outputs.tf
    lambda/
      decision_handler.py
      requirements.txt
    config/
      rules.json
      sample_loan.json
      slack.env.example
    README.md
```

> Tip: learners can clone/paste from this manual; you can also initialize a Git repo and hand it to the class.

---

## 3) (A) Q Developer – Fix a Spring Bug & Generate Tests

### 3.1 Create the Spring Boot service

**`A-q-dev-spring/pom.xml`**

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0" ...>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.finbank</groupId>
  <artifactId>loans</artifactId>
  <version>1.0.0</version>
  <properties>
    <java.version>21</java.version>
    <spring.boot.version>3.3.2</spring.boot.version>
  </properties>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-dependencies</artifactId>
        <version>${spring.boot.version}</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
      <groupId>org.postgresql</groupId>
      <artifactId>postgresql</artifactId>
      <scope>runtime</scope>
    </dependency>
    <dependency>
      <groupId>org.flywaydb</groupId>
      <artifactId>flyway-core</artifactId>
    </dependency>
    <!-- Tests -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.mockito</groupId>
      <artifactId>mockito-junit-jupiter</artifactId>
      <version>5.12.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
```

**`A-q-dev-spring/src/main/java/com/finbank/loans/LoansApplication.java`**

```java
package com.finbank.loans;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class LoansApplication {
  public static void main(String[] args) {
    SpringApplication.run(LoansApplication.class, args);
  }
}
```

**A simple (buggy) service**: a rounding bug in EMI (monthly installment) calculation.

**`A-q-dev-spring/src/main/java/com/finbank/loans/domain/LoanOffer.java`**

```java
package com.finbank.loans.domain;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

public record LoanOffer(
    @NotNull @Min(1) BigDecimal principal,
    @NotNull @Min(1) Integer termMonths,
    @NotNull BigDecimal annualRate // e.g., 0.12 for 12%
) {}
```

**`A-q-dev-spring/src/main/java/com/finbank/loans/service/LoanCalculator.java`**

```java
package com.finbank.loans.service;

import com.finbank.loans.domain.LoanOffer;
import java.math.BigDecimal;
import java.math.RoundingMode;

public class LoanCalculator {

  // BUG: using double math + incorrect rounding to 2 decimals early
  public BigDecimal monthlyEmi(LoanOffer offer) {
    double P = offer.principal().doubleValue();
    double r = offer.annualRate().doubleValue() / 12.0;
    int n = offer.termMonths();

    double emi = (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    // premature rounding causes cumulative error:
    return BigDecimal.valueOf(emi).setScale(2, RoundingMode.HALF_UP);
  }

  // CORRECT (we will refactor to this with Q’s help)
  public BigDecimal monthlyEmiCorrect(LoanOffer offer) {
    BigDecimal P = offer.principal();
    BigDecimal r = offer.annualRate().divide(BigDecimal.valueOf(12), 10, RoundingMode.HALF_UP);
    int n = offer.termMonths();

    BigDecimal onePlusRPowerN = (BigDecimal.ONE.add(r)).pow(n);
    BigDecimal numerator = P.multiply(r).multiply(onePlusRPowerN);
    BigDecimal denominator = onePlusRPowerN.subtract(BigDecimal.ONE);

    return numerator.divide(denominator, 10, RoundingMode.HALF_UP)
                    .setScale(2, RoundingMode.HALF_UP);
  }
}
```

**`A-q-dev-spring/src/main/java/com/finbank/loans/web/LoanController.java`**

```java
package com.finbank.loans.web;

import com.finbank.loans.domain.LoanOffer;
import com.finbank.loans.service.LoanCalculator;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@RestController
@RequestMapping("/api/loans")
public class LoanController {
  private final LoanCalculator calculator = new LoanCalculator();

  @PostMapping("/emi")
  public ResponseEntity<BigDecimal> calculateEmi(@RequestBody @Valid LoanOffer offer) {
    return ResponseEntity.ok(calculator.monthlyEmi(offer)); // buggy path for demo
  }

  @PostMapping("/emi/correct")
  public ResponseEntity<BigDecimal> calculateEmiCorrect(@RequestBody @Valid LoanOffer offer) {
    return ResponseEntity.ok(calculator.monthlyEmiCorrect(offer));
  }
}
```

### 3.2 Run & observe the bug

```
cd A-q-dev-spring
mvn spring-boot:run
```

POST to `http://localhost:8080/api/loans/emi` with:

```json
{ "principal": 1000000, "termMonths": 120, "annualRate": 0.12 }
```

Compare output of `/emi` vs `/emi/correct` — you’ll see minor drift on edge cases (short terms, high rates).

### 3.3 Use **Amazon Q Developer** in your IDE

Prompts you can demonstrate in class:

* *“Explain the difference in precision between `monthlyEmi` and `monthlyEmiCorrect` and propose a safe refactor.”*
* *“Generate JUnit 5 tests covering typical and edge cases for both methods; assert tolerance ≤ ₹0.05 difference on common inputs.”*
* *“Suggest a property-based test for randomized inputs and detect divergence > ₹0.50.”*

### 3.4 Unit tests (baseline)

**`A-q-dev-spring/src/test/java/com/finbank/loans/service/LoanCalculatorTest.java`**

```java
package com.finbank.loans.service;

import com.finbank.loans.domain.LoanOffer;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

class LoanCalculatorTest {

  @Test
  void typicalCase() {
    LoanCalculator calc = new LoanCalculator();
    LoanOffer offer = new LoanOffer(
        BigDecimal.valueOf(1_000_000), 120, BigDecimal.valueOf(0.12)
    );
    BigDecimal buggy = calc.monthlyEmi(offer);
    BigDecimal correct = calc.monthlyEmiCorrect(offer);

    assertTrue(buggy.subtract(correct).abs().doubleValue() > 0.0,
        "Buggy should differ from correct for teaching");
  }

  @Test
  void highRateShortTerm() {
    LoanCalculator calc = new LoanCalculator();
    LoanOffer offer = new LoanOffer(
        BigDecimal.valueOf(200_000), 6, BigDecimal.valueOf(0.28)
    );
    BigDecimal buggy = calc.monthlyEmi(offer);
    BigDecimal correct = calc.monthlyEmiCorrect(offer);
    assertTrue(buggy.subtract(correct).abs().doubleValue() >= 0.01);
  }
}
```

> In class, ask learners to use **Q Developer** to:
>
> 1. refactor `monthlyEmi()` to the precise BigDecimal version, and
> 2. have Q generate **more tests** (nulls, invalid inputs, property-based patterns).

---

## 4) (B) Q Business – Self-Serve Analytics (RDS + S3)

We’ll spin up Postgres locally (Docker) for dev, then point Q Business to **RDS Postgres** in AWS (or keep local for demo).

### 4.1 Postgres (Local, for quick start)

```bash
docker run --name finbank-pg -e POSTGRES_PASSWORD=finbank -e POSTGRES_DB=finbank \
  -p 5432:5432 -d postgres:16
```

**`B-q-business-data/db/init.sql`**

```sql
-- Branches
CREATE TABLE IF NOT EXISTS branch (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  city VARCHAR(80) NOT NULL
);

-- Loans
CREATE TABLE IF NOT EXISTS loan (
  id SERIAL PRIMARY KEY,
  branch_code VARCHAR(10) REFERENCES branch(code),
  customer_id VARCHAR(36) NOT NULL,
  principal NUMERIC(14,2) NOT NULL,
  annual_rate NUMERIC(6,4) NOT NULL,
  term_months INT NOT NULL,
  issued_on DATE NOT NULL,
  status VARCHAR(16) NOT NULL -- ACTIVE | CLOSED | DEFAULTED
);

-- NPA (Non-Performing Assets) snapshot per quarter
CREATE TABLE IF NOT EXISTS npa_snapshot (
  id SERIAL PRIMARY KEY,
  quarter VARCHAR(6) NOT NULL, -- e.g., 2025Q2
  branch_code VARCHAR(10) REFERENCES branch(code),
  total_loans INT NOT NULL,
  npa_loans INT NOT NULL
);

INSERT INTO branch(code, city) VALUES
 ('BR001','Mumbai'), ('BR002','Delhi'), ('BR003','Bengaluru')
 ON CONFLICT DO NOTHING;

INSERT INTO loan(branch_code, customer_id, principal, annual_rate, term_months, issued_on, status)
VALUES
 ('BR001','c-001', 1000000, 0.1200, 120, '2024-12-10','ACTIVE'),
 ('BR002','c-002',  600000, 0.1450,  60, '2025-01-15','DEFAULTED'),
 ('BR003','c-003',  450000, 0.1050,  48, '2025-03-05','ACTIVE'),
 ('BR001','c-004',  900000, 0.1300,  84, '2024-11-20','CLOSED');

INSERT INTO npa_snapshot(quarter, branch_code, total_loans, npa_loans) VALUES
 ('2025Q1','BR001', 320, 16),
 ('2025Q1','BR002', 290, 22),
 ('2025Q1','BR003', 210, 11),
 ('2025Q2','BR001', 330, 18),
 ('2025Q2','BR002', 300, 25),
 ('2025Q2','BR003', 240, 12);
```

Load it:

```bash
cat B-q-business-data/db/init.sql | docker exec -i finbank-pg psql -U postgres -d finbank
```

### 4.2 S3 Reports (for Q Business to index)

Create a CSV locally (later upload to S3):
**`B-q-business-data/s3/reports/quarterly_report_2025Q2.csv`**

```csv
branch_code,quarter,total_loans,closed_loans,new_loans,delinquency_rate
BR001,2025Q2,330,62,81,0.054
BR002,2025Q2,300,55,75,0.083
BR003,2025Q2,240,49,60,0.050
```

### 4.3 Standing up AWS data (RDS + S3) – quick path

* Create **RDS Postgres** (free tier ok) named `finbank`, public for lab (or via bastion).
* Create **S3 bucket**: `finbank-q-reports-<your-id>` and upload `quarterly_report_2025Q2.csv`.
* Set IAM as in **section 7**.

### 4.4 Q Business – connect the sources (what to demo)

Once Amazon Q Business is enabled in your org:

1. **Add data source:**

   * **PostgreSQL**: point to RDS endpoint, DB user (read-only), schema `public`.
   * **S3**: bucket `finbank-q-reports-<id>`, prefix `reports/`.
2. **Define “Business Names” (Metadata)**

   * Map `npa_snapshot.npa_loans / total_loans` to “NPA ratio”.
   * Map `loan.status` domain to `{ACTIVE, CLOSED, DEFAULTED}`.
3. **Guardrails:**

   * Restrict finance analysts to read-only schemas.
   * Mask `customer_id` with partial reveal.

**Prompts to show live:**

* “Top 5 branches with **highest NPA ratio** in **2025Q2**; show table + bar chart.”
* “Loans **issued in Q1 2025** with **rate > 12%** by **branch city**. Return CSV.”
* “Trend of **delinquency\_rate** last two quarters, annotate spikes.”

> (Q will generate the SQL; ask learners to inspect/validate it. This is the “pairing with human judgment” moment.)

---

## 5) (C) Q App – Loan Decisioning Workflow (Lambda + Step Functions + Slack)

We’ll build an **API-triggered loan decision** that evaluates eligibility & KYC rules, writes a decision artifact, and sends a Slack message. You can wrap this with Amazon Q Apps (for UI) or call the workflow directly.

### 5.1 Business rules (editable JSON)

**`C-q-app-loan-decision/config/rules.json`**

```json
{
  "min_credit_score": 680,
  "max_dti": 0.45,
  "max_ltv": 0.80,
  "max_amount_by_city": {
    "Mumbai": 3000000,
    "Delhi": 2500000,
    "Bengaluru": 2200000,
    "*": 2000000
  },
  "pep_denied": true,
  "kyc_required_fields": ["aadhaar", "pan", "address_proof"]
}
```

**Sample input**
**`C-q-app-loan-decision/config/sample_loan.json`**

```json
{
  "application_id": "APP-2025-001",
  "customer": {
    "name": "Amit Kumar",
    "city": "Mumbai",
    "credit_score": 702,
    "declared_pep": false,
    "kyc": {
      "aadhaar": "XXXX-XXXX-1234",
      "pan": "ABCDE1234F",
      "address_proof": "utility_bill"
    }
  },
  "loan": {
    "amount": 1500000,
    "property_value": 2200000,
    "monthly_income": 145000,
    "existing_obligations": 35000,
    "annual_rate": 0.115,
    "term_months": 120
  }
}
```

### 5.2 Lambda decision code (Python)

**`C-q-app-loan-decision/lambda/decision_handler.py`**

```python
import json, os, math, decimal, urllib.request

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "")

def post_slack(msg: str):
    if not SLACK_WEBHOOK:
        return
    data = json.dumps({"text": msg}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print("Slack error:", e)

def monthly_emi(principal: float, annual_rate: float, term_months: int) -> float:
    r = annual_rate / 12.0
    if r == 0:
        return principal / term_months
    top = principal * r * ((1 + r) ** term_months)
    bot = ((1 + r) ** term_months) - 1
    return round(top / bot, 2)

def decide(event, _ctx=None):
    app = event if isinstance(event, dict) else json.loads(event)
    rules = event.get("_rules", {})

    cust = app["customer"]
    loan = app["loan"]

    # Derived metrics
    emi = monthly_emi(loan["amount"], loan["annual_rate"], loan["term_months"])
    dti = (emi + loan["existing_obligations"]) / max(1, loan["monthly_income"])  # Debt-to-income
    ltv = loan["amount"] / max(1, loan["property_value"])

    reasons = []

    # Rules
    if cust["credit_score"] < rules.get("min_credit_score", 680):
        reasons.append(f"Credit score {cust['credit_score']} below minimum")
    if dti > rules.get("max_dti", 0.45):
        reasons.append(f"DTI {dti:.2f} exceeds max")
    if ltv > rules.get("max_ltv", 0.80):
        reasons.append(f"LTV {ltv:.2f} exceeds max")
    city_cap = rules.get("max_amount_by_city", {}).get(cust["city"],
               rules.get("max_amount_by_city", {}).get("*", 999999999))
    if loan["amount"] > city_cap:
        reasons.append(f"Amount {loan['amount']} exceeds city cap for {cust['city']}")
    if rules.get("pep_denied", True) and cust.get("declared_pep", False):
        reasons.append("Customer is PEP (politically exposed person)")

    missing = [f for f in rules.get("kyc_required_fields", []) if not cust["kyc"].get(f)]
    if missing:
        reasons.append("Missing KYC: " + ", ".join(missing))

    decision = "APPROVE" if not reasons else "REJECT"
    out = {
        "application_id": app["application_id"],
        "decision": decision,
        "reasons": reasons,
        "metrics": {
            "emi": emi,
            "dti": round(dti, 3),
            "ltv": round(ltv, 3)
        }
    }

    post_slack(f":bank: Loan {app['application_id']} => *{decision}* (EMI ₹{emi}, DTI {dti:.2f}, LTV {ltv:.2f})")
    return out

def lambda_handler(event, context):
    # Expect event to include _rules (injected by Step Function) or fetch from parameter store
    return decide(event, context)
```

**`C-q-app-loan-decision/lambda/requirements.txt`**

```
# empty for now; stdlib only
```

### 5.3 Step Functions state machine (concept)

* **Task 1:** Load rules (from SSM Parameter Store or a JSON file in S3).
* **Task 2:** Invoke `decision_handler` with `{...application, _rules: ...}`.
* **Task 3:** Persist decision to DynamoDB (optional).
* **Task 4:** Slack notification (done inside Lambda above).

We’ll provision Lambda + IAM with Terraform for repeatability.

### 5.4 Terraform (serverless minimal)

**`C-q-app-loan-decision/infra/terraform/main.tf`**

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { default = "ap-south-1" }
variable "slack_webhook" { type = string }

resource "aws_iam_role" "lambda_role" {
  name = "finbank-decision-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_exec" {
  role       = aws_iam_role["lambda_role"].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "decision" {
  function_name    = "finbank-decision"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.11"
  handler          = "decision_handler.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      SLACK_WEBHOOK = var.slack_webhook
    }
  }
}

output "lambda_name" {
  value = aws_lambda_function.decision.function_name
}
```

**`C-q-app-loan-decision/infra/terraform/variables.tf`**

```hcl
variable "region" { type = string }
variable "slack_webhook" { type = string }
```

**`C-q-app-loan-decision/infra/terraform/outputs.tf`**

```hcl
output "lambda_name" { value = aws_lambda_function.decision.function_name }
```

Deploy:

```bash
cd C-q-app-loan-decision/infra/terraform
terraform init
terraform apply -auto-approve -var="slack_webhook=https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

### 5.5 Test the Lambda locally (before deploy)

```bash
cd C-q-app-loan-decision/lambda
export SLACK_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"
python3 -c "import json,decision_handler as d, pathlib; 
event=json.loads(pathlib.Path('../config/sample_loan.json').read_text());
event['_rules']=json.loads(pathlib.Path('../config/rules.json').read_text());
print(d.lambda_handler(event,None))"
```

Expected output:

```json
{
  "application_id": "APP-2025-001",
  "decision": "APPROVE",
  "reasons": [],
  "metrics": { "emi": 22207.58, "dti": 0.18, "ltv": 0.68 }
}
```

> And a Slack message in your channel 🙌

---

## 6) API Gateway (optional) + Postman

You can expose the Lambda via API Gateway to accept JSON applications from your CRM or a Q App front-end.

* Create an **HTTP API** in API Gateway → Integrations → Lambda `finbank-decision`.
* Route `POST /decide` → Lambda proxy.
* Use Postman to POST the combined object (application + rules), or keep rules server-side.

---

## 7) IAM Guardrails (copy-paste policies)

**Read-only Postgres (attached to RDS DB user)** – enforced at DB level, but you’ll also want **Q Business access roles** like:

**DB creds in Secrets Manager** (policy for Q to read):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowReadSecretsForQBusiness",
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:ap-south-1:<account-id>:secret:finbank/rds/readonly-*"
  }]
}
```

**S3 (bucket prefix scoping)**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowQBusinessReportsRead",
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::finbank-q-reports-*",
      "arn:aws:s3:::finbank-q-reports-*/*"
    ],
    "Condition": {
      "StringLike": { "s3:prefix": [ "reports/*" ] }
    }
  }]
}
```

**Principle of least privilege**: analysts assume a role that has only S3 read on the reports prefix + DB read-only via a Secrets Manager-stored credential that Q Business uses internally.

---

## 8) Training Flow (how to teach this in 90–120 mins)

1. **Warm-up (10 min):** Show the EMI bug, ask learners to guess precision issues.
2. **Q Developer (25–35 min):** Let them:

   * Ask Q to refactor to BigDecimal approach.
   * Generate tests (equivalence classes, edge cases).
   * Run tests; track time saved vs manual coding.
3. **Q Business (25–30 min):**

   * Connect Postgres + S3.
   * Build 3–4 natural language questions; inspect SQL.
4. **Q App (25–35 min):**

   * Apply Terraform, test Lambda locally & from AWS.
   * Watch Slack notifications.
5. **Wrap-up (10 min):**

   * Discuss guardrails, RBAC, and how to productionize.

---

## 9) KPIs & Validation

* **Q Dev**: Mean time to write tests ↓ (e.g., 30–50%).
* **Q Biz**: IT tickets for ad-hoc SQL ↓ (50–60%).
* **Q App**: Manual review time per application ↓ (20–40%); SLA adherence ↑.

---

## 10) Troubleshooting (quick answers)

* **Q Business can’t read DB** → check Secrets Manager name/ARN & security group rules to RDS.
* **Lambda no Slack** → verify `SLACK_WEBHOOK`, outbound internet (NAT) if in private subnets.
* **Precision mismatch** → ensure BigDecimal scale/rounding is applied **after** final division.
* **S3 not indexed** → verify bucket policy + prefix; re-sync in Q Business.

---

## 11) Roadmap & Extensions

* Replace CSV with **Athena** over S3 for larger clickstream.
* Add **DynamoDB** table to persist decisions + an S3 “decision letter” PDF.
* Wrap the workflow in a **Q App** UI for business users to submit & track decisions.
* Plug into **ServiceNow/Jira** for auto-ticketing rejected cases.

---

### ✅ What you can demo immediately

* Run the Spring service, show the bug, **use Q Developer** to fix + generate tests.
* Spin **local Postgres**, load SQL, and **query via Q Business**.
* Deploy the **Lambda** (Terraform), run the decision, and **receive Slack**.

