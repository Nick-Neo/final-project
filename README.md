# POSHub Cloud Store

A cloud-native e-commerce platform for Point-of-Sale (POS) hardware built using Flask, Microsoft Azure, Docker, Kubernetes (AKS), Azure MySQL, Azure Blob Storage, and Stripe.

This project was developed as part of the Generation Singapore Cloud Support & DevOps Bootcamp Final Project and demonstrates modern cloud deployment, containerization, DevOps automation, payment integration, database management, and role-based web application development.

---

## Project Overview

POSHub Cloud Store is an online platform that allows customers to browse and purchase POS hardware while enabling administrators to manage products, inventory, orders, and customer support requests through a dedicated admin portal.

The application is fully containerized using Docker and deployed on Azure Kubernetes Service (AKS) with automated CI/CD pipelines.

---

## Key Features

### Customer Features

- User Registration and Login
- Secure Authentication
- Product Browsing and Search
- Product Detail Pages
- Shopping Cart Management
- Stripe Payment Integration
- Order Placement and Tracking
- Customer Dashboard
- Support Ticket Submission

### Admin Features

- Admin Dashboard
- Product Management
- Inventory Management
- Add/Edit/Delete Products
- Azure Blob Storage Image Upload
- Support Ticket Management
- Order Monitoring
- Role-Based Access Control

### Cloud & DevOps Features

- Docker Containerization
- Azure Kubernetes Service (AKS)
- Azure Container Registry (ACR)
- Azure MySQL Flexible Server
- Azure Blob Storage
- Automated CI/CD Pipeline
- Kubernetes Secrets Management
- Load Balanced Deployment
- Rolling Updates

---

## System Architecture

```text
┌─────────────────────┐
│      Customer       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Azure Load Balancer │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Azure Kubernetes Service (AKS)   │
│ Flask + Gunicorn Application     │
└──────────┬───────────┬───────────┘
           │           │
           │           │
           ▼           ▼

 Azure MySQL      Azure Blob Storage
 Flexible Server  Product Images

           │
           ▼

       Stripe
 Payment Gateway
```

---

## Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

### Backend

- Python
- Flask
- SQLAlchemy
- Flask-Login
- Gunicorn

### Database

- Azure Database for MySQL Flexible Server

### Cloud Services

- Microsoft Azure
- Azure Kubernetes Service (AKS)
- Azure Container Registry (ACR)
- Azure Blob Storage

### DevOps

- Docker
- Kubernetes
- Azure DevOps Pipelines
- GitHub
- Azure CLI

### Payment Processing

- Stripe Checkout
- Stripe Webhooks

---

## Project Structure

```text
final-project/
│
├── static/
│   ├── css/
│   ├── js/
│   ├── uploads/
│   └── assets/
│
├── templates/
│   ├── customer/
│   └── admin/
│
├── app.py
├── models.py
├── requirements.txt
├── Dockerfile
├── gunicorn.conf.py
├── azure-pipelines.yml
├── deployment.yaml
├── service.yaml
└── README.md
```

---

## Database Design

### Users

| Field | Description |
|---------|-------------|
| id | User ID |
| username | Username |
| email | User Email |
| password_hash | Encrypted Password |
| role | Customer/Admin |

### Inventory Items

| Field | Description |
|---------|-------------|
| id | Product ID |
| item_name | Product Name |
| category | Product Category |
| description | Product Description |
| quantity_left | Available Stock |
| price | Product Price |
| image_url | Azure Blob Image URL |

### Orders

| Field | Description |
|---------|-------------|
| id | Order ID |
| user_id | Customer ID |
| total_price | Order Amount |
| created_at | Order Date |

### Order Items

| Field | Description |
|---------|-------------|
| id | Item ID |
| order_id | Order Reference |
| inventory_item_id | Product Reference |
| quantity | Quantity Purchased |

### Support Tickets

| Field | Description |
|---------|-------------|
| id | Ticket ID |
| user_id | Customer ID |
| subject | Ticket Subject |
| message | Ticket Details |
| status | Open/Closed |

---

## CI/CD Pipeline

The application uses Azure DevOps to automate build and deployment processes.

### Pipeline Flow

```text
GitHub Push
      │
      ▼
Azure Pipeline Trigger
      │
      ▼
Docker Build
      │
      ▼
Push Image to ACR
      │
      ▼
Update Deployment Manifest
      │
      ▼
Deploy to AKS
      │
      ▼
Rolling Update
```

### CI/CD Components

- Source Control: GitHub
- Build Automation: Azure Pipelines
- Container Registry: Azure Container Registry (ACR)
- Deployment Platform: Azure Kubernetes Service (AKS)

---

## Stripe Payment Integration

Stripe is used to securely process customer payments.

### Payment Workflow

```text
Customer Checkout
        │
        ▼
Stripe Checkout Session
        │
        ▼
Secure Payment Processing
        │
        ▼
Stripe Webhook Verification
        │
        ▼
Order Confirmation
        │
        ▼
Database Update
```

### Security Features

- PCI-compliant payment processing
- Hosted Stripe Checkout
- Webhook verification
- No payment card data stored within the application

---

## Azure Services Used

| Service | Purpose |
|----------|----------|
| Azure Kubernetes Service (AKS) | Application Hosting |
| Azure Container Registry (ACR) | Container Image Storage |
| Azure MySQL Flexible Server | Database |
| Azure Blob Storage | Product Image Storage |
| Azure Load Balancer | Traffic Distribution |

---

## Deployment

### Build Docker Image

```bash
docker build -t poshub .
```

### Run Locally

```bash
docker run -p 8000:8000 poshub
```

### Deploy to Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Verify Deployment

```bash
kubectl get pods

kubectl get svc

kubectl get deployments
```

---

## Environment Variables

```env
SECRET_KEY=

DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

AZURE_STORAGE_CONNECTION_STRING=
AZURE_CONTAINER_NAME=

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

MAIL_SERVER=
MAIL_PORT=
MAIL_USERNAME=
MAIL_PASSWORD=

SUPPORT_EMAIL=
```

---

## Screenshots

### Customer Portal

- Home Page
- Product Catalog
- Product Details
- Shopping Cart
- Checkout Page

### Admin Portal

- Dashboard
- Inventory Management
- Product Management
- Support Ticket Management

> Add screenshots here for better presentation and recruiter visibility.

---

## Learning Outcomes

This project provided practical experience in:

- Cloud Infrastructure Deployment
- Kubernetes Administration
- Containerization with Docker
- CI/CD Automation
- Azure Services Integration
- Secure Payment Gateway Integration
- Database Design and Management
- Role-Based Authentication
- Web Application Development
- Cloud-Native Architecture
- Production Deployment Practices

---

## Future Enhancements

- Email Order Confirmation
- Customer Order History Dashboard
- Product Reviews and Ratings
- Azure Monitor Integration
- Log Analytics Dashboard
- Redis Caching
- Horizontal Pod Autoscaling (HPA)
- Multi-Region Deployment
- Advanced Reporting Dashboard

---

## Live Demo

**Application URL**

http://finalprojectepos.southeastasia.cloudapp.azure.com

---

## Author

**Kai Siang**
**Nicky Neo**
**Khalis B**
**Wilson O**

Generation Singapore Cloud Support & DevOps Bootcamp

GitHub: https://github.com/kaisiang419
        https://github.com/Nick-Neo
        https://github.com/mkbmr
        https://github.com/wilsonongcc8-ui

---

## Acknowledgements

This project was developed as part of the Generation Singapore Cloud Support & DevOps Bootcamp, combining cloud infrastructure, DevOps practices, containerization, payment processing, and full-stack web development into a production-ready application.
