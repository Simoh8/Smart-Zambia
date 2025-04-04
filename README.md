How to Setup Smart Zambia Invoice

# Smart Invoice – Configuration Settings

The **Smart Invoice** app integrates with the **ZRA (Zambia Revenue Authority)** system to facilitate the issuance of electronic fiscal invoices (Smart Invoices). Below are the configuration settings that must be properly set up to ensure smooth integration and compliance.

---

## Environment Configuration

### 🔁 SandBox/Test Environment (`sandboxtest_environment_`)
- **Description:** This is a secure test environment provided by ZRA.
- **Purpose:** Used during the testing phase to validate API integrations.
- **Note:** It simulates live functionalities without affecting actual taxpayer data.

---

### ✅ Production Environment (`production_environment_`)
- **Description:** This is the **live** environment used for real-time invoice issuance.
- **Purpose:** API calls here interact with actual ZRA systems and taxpayer data.
- **Note:** Only enable this after successfully completing testing in the sandbox environment.

---

### 🌐 Server URL (`server_url`)
- **Description:** The base URL for ZRA API requests.
- **Example:**
  - Sandbox: `http://localhost:8080/zrasandboxvsdc`
  - Production: (as provided by ZRA)
- **Usage:** Should correspond to the selected environment.

---

### 🔘 Is Active (`is_active_`)
- **Description:** Toggle to enable or disable Smart Invoice integration.
- **Purpose:** Allows temporary disabling without losing settings.

---

### 🌍 Environment (`environment`)
- **Options:** `Sandbox`, `Production`
- **Description:** Defines the operating environment for the app.
- **Purpose:** Determines the endpoint behavior and data handling.

---

## Accounting Configuration

### 🧾 Auto Create Branch Accounting Dimension (`auto_create_branch_accounting_dimension`)
- **Description:** When enabled, this automatically creates a **Branch** accounting dimension.
- **Purpose:** Helps track P&L (Profit and Loss) per branch.
- **Recommendation:** It is advised to keep this enabled for businesses with multiple branches.

---

## Company & Branch Details

### 🏢 Company Name (`company_name`)
- **Description:** ERPNext company name to be used in invoices.
- **Input:** Must match the company profile within your ERP system.

---

### 🏢 ZRA Company Name (`zra_company_name`)
- **Description:** Official company name as registered with ZRA.
- **Note:** This must exactly match the name on the ZRA portal for compliance.

---

### 🔢 Company TPIN (`company_tpin`)
- **Description:** Taxpayer Identification Number registered with ZRA.
- **Format:** 9-digit numeric (e.g., `1017138037`)

---

### 🌍 Country (`country`)
- **Description:** The operating country for the company.
- **Default:** Zambia

---

### 🏬 Branch Name (`branch_name`)
- **Description:** Name of the branch issuing invoices.

---

### 🆔 Branch ID (`branch_id`)
- **Description:** Unique identifier assigned to each branch by ZRA.
- **Note:** Must correspond to the branch registration on the ZRA system.

---

### 🔒 VSDC Device Serial Number (`vsdc_device_serial_number`)
- **Description:** Serial number of the **Virtual Sales Data Controller (VSDC)** device provided by ZRA.
- **Purpose:** Required for invoice validation and authentication during submission.

---

Let me know if you’d like this turned into a README.md format or integrated into your ERPNext app as in-app field tooltips or help texts.