# 🇿🇲 Smart Invoice Zambia – Setup Guide

The **Smart Invoice Zambia** app integrates ERPNext with the **Zambia Revenue Authority (ZRA)** Smart Invoicing system, enabling real-time, compliant invoice submissions.

This guide walks you through the necessary steps to get started.

---

## ✅ Prerequisites

Before starting, ensure:

- ✅ You have at least **one branch set up on the ZRA Portal**: [https://www.zra.org.zm/](https://www.zra.org.zm/)
- ✅ Your **VSDC Device** has been provisioned by ZRA.
- ✅ You have the following details from ZRA:
  - **Branch ID**
  - **VSDC Device Serial Number**

---

## ⚙️ Step 1: Configure ZRA Smart Invoice Settings

Go to **ZRA Smart Invoice Settings** in your ERPNext system and fill out the following fields:

### 🔧 Environment Settings

| Label                     | Description |
|--------------------------|-------------|
| **SandBox/Test Environment** | Enable to use ZRA's test environment. |
| **Production Environment** | Enable when ready to send live invoices. |
| **Server URL**           | Enter the ZRA API URL (based on selected environment). |
| **Is Active**            | Toggle to enable or disable Smart Invoice integration. |
| **Environment**          | Choose `Sandbox` or `Production`. |

### 💼 Accounting & Company Details

| Label                                      | Description |
|-------------------------------------------|-------------|
| **Auto Create Branch Accounting Dimension** | Automatically adds branch tracking to accounting reports. |
| **Company Name**                          | Link your ERPNext company. |
| **ZRA Company Name**                      | Official company name registered with ZRA. |
| **Company TPIN**                          | Your ZRA-issued Taxpayer Identification Number. |
| **Country**                               | Set to `Zambia`. |
| **Branch Name**                           | Local branch name. |
| **Branch ID**                             | ZRA-assigned Branch ID. |
| **VSDC Device Serial Number**             | Serial number of your ZRA-provided VSDC device. |

> ⚠️ **Important:** All values must match what’s on the ZRA portal exactly.

---

## ⚡ Step 2: Fetch ZRA Codes

After saving the Smart Invoice Settings, do the following:

1. Click on the **ZRA Actions** dropdown at the top right of the form.
2. Select:
   - **Get Standard Codes** – Fetches ZRA default tax types, industry codes, etc.
   - **Get Item Codes** – Loads item classification codes required for compliance.

These actions run in the background and prepare your system for real-time syncing.

---

## 👤 Step 3: Create Walk-In Customer (Optional)

To handle cash sales or customers without a TPIN:

1. Create a customer named `Walk-in Customer` (or similar).
2. Set their **Tax ID (TPIN)** to: 1000000000


> This is ZRA's default TPIN for unidentified customers.

---

## ✅ Step 4: Go Live

With everything configured, you can now:

- 🔐 Register branch users.
- 🧾 Start creating **Sales Invoices** and **Purchase Invoices**.
- 🚀 Submit them to ZRA automatically and in compliance.

---

## 🧠 Notes

- Always start with **Sandbox** testing before moving to **Production**.
- Ensure your server can reach the ZRA API endpoints.
- For organizations with multiple branches, repeat the setup per branch using unique **Branch IDs** and **VSDC Serial Numbers**.

---

## 📞 Support

For help or troubleshooting, please contact your ERP administrator or raise an issue on this repository.

---
