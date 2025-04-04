Absolutely! Here’s an expanded and more structured version of your setup instructions for the **Smart Invoice Zambia** app, written in a user-friendly and professional "Getting Started" format:

---

# 🚀 Getting Started with the Smart Invoice Zambia App

This guide walks you through the **initial setup steps** required to successfully configure and start using the **Smart Invoice Zambia** app, which integrates with the **Zambia Revenue Authority (ZRA)** for compliant e-invoicing.

---

## ✅ Prerequisites

Before setting up the app, make sure the following is done:

### 🔹 1. ZRA Portal Setup
- You **must have at least one branch registered** on the [ZRA e-invoicing portal](https://www.zra.org.zm/).
- Ensure your **VSDC device** is provisioned and linked to your registered branch.
- Obtain your **Branch ID** and **VSDC Device Serial Number** from the ZRA portal.

---

## ⚙️ Step 1: Configure Smart Invoice Settings

Navigate to **ZRA Smart Invoice Settings** in your ERP system, and fill in the required fields:

### Environment Settings:
- **SandBox/Test Environment:** Enable for testing in ZRA’s sandbox environment.
- **Production Environment:** Enable when ready to send live data to ZRA.
- **Server URL:** Enter the correct ZRA API URL based on the environment (e.g., sandbox or production).
- **Is Active:** Toggle to activate Smart Invoice functionality.
- **Environment:** Choose between `Sandbox` and `Production`.

### Accounting & System Settings:
- **Auto Create Branch Accounting Dimension:** Enable to automatically create a branch dimension for tracking financials per branch.

### Company and Branch Details:
- **Company Name:** Select your ERPNext company.
- **ZRA Company Name:** Enter the official name as registered with ZRA.
- **Company TPIN:** Enter your ZRA-issued TPIN.
- **Country:** Set to `Zambia`.
- **Branch Name:** Provide your branch's local name.
- **Branch ID:** Use the ID provided by ZRA for this branch.
- **VSDC Device Serial Number:** Enter the device serial number assigned by ZRA.

> 📝 **Tip:** All details must match your ZRA portal records exactly for proper API communication.

---

## ⚡ Step 2: Load Standard ZRA Codes

Once the **ZRA Smart Invoice Settings** are saved:

1. Look for a dropdown button called **"ZRA Actions"** on the same settings form.
2. Click on:
   - ✅ **Get Standard Codes** – This fetches default tax types, units of measure, and industry classifications required for ZRA integration.
   - ✅ **Get Item Codes** – This fetches product codes and classifications used in item mapping.

> These operations run in the background and prepare your system for compliance with ZRA data requirements.

---

## 👤 Step 3: Add a Default "Walk-In" Customer

For retail or cash sales where the customer doesn’t have a TPIN:

1. Create a new customer named `Walk-in Customer` (or similar).
2. Set the **Tax ID (TPIN)** of the customer to:  
   ```
   1000000000
   ```

> This is the **ZRA-provided default TPIN** for unidentified or non-registered customers.

---

## ✅ Step 4: You're Ready!

With the setup complete, you can now proceed to:
- ✅ Register **branch users** and associate them with the branch.
- ✅ Start issuing **Sales Invoices** and **Purchase Invoices** that will sync with ZRA in real time.
- ✅ Monitor invoice status and communication logs within your ERP system.

---

## 🧠 Notes

- Always start in **Sandbox mode** for testing before switching to **Production**.
- Make sure your server has internet access and can reach the ZRA endpoints.
- For multiple branches, repeat the setup steps per branch, each with its own **Branch ID** but same  **VSDC Serial**.

---

Let me know if you'd like this formatted as a README.md for your app repo or converted into an ERPNext Help Article!