# AI-Based Waterborne Disease Monitoring and Outbreak Prediction System
**Final Year Project Report**

---

## 1. ABSTRACT

Waterborne diseases pose a significant threat to global public health, particularly in developing regions with inadequate sanitation infrastructure. Traditional water quality monitoring methods rely heavily on manual sampling and delayed laboratory analysis, which are insufficient for preventing large-scale outbreaks. 

This project presents "AquaCare," a comprehensive AI-Based Waterborne Disease Monitoring and Outbreak Prediction System. The proposed solution integrates computer vision, machine learning, and real-time data analytics to continuously monitor water quality and predict disease outbreaks. A hybrid image analysis engine combining Ultralytics YOLOv8 and Smart Computer Vision techniques is used to instantly identify physical water contaminants (e.g., industrial waste, sewage, algal blooms) from visual feeds. Simultaneously, a Random Forest machine learning model analyzes multi-dimensional sensor data (pH, turbidity, dissolved oxygen, bacteria counts) to predict localized outbreak probabilities for diseases such as Cholera, Typhoid, and Diarrhea.

The system is deployed as a full-stack web application featuring a React-based interactive dashboard, a Flask backend, and a MongoDB database for persistent telemetry storage. An automated alert system integrates Twilio SMS and web notifications to dispatch real-time warnings to relevant health authorities when critical risk thresholds are exceeded. By shifting from reactive medical responses to proactive environmental surveillance, this system provides a highly scalable and cost-effective framework for early outbreak intervention.

---

## 2. INTRODUCTION

### Background of Waterborne Diseases
Waterborne diseases are illnesses caused by pathogenic microorganisms transmitted through contaminated fresh water. According to the World Health Organization (WHO), diseases such as cholera, typhoid, and diarrheal illnesses account for millions of deaths annually. These outbreaks are frequently triggered by sudden environmental changes, structural failures in sanitation, or the uncontrolled dumping of industrial waste into public water bodies.

### Need for Monitoring Systems
The traditional approach to water safety involves collecting physical samples and transporting them to laboratories for chemical and biological assays. This process can take anywhere from 24 to 72 hours. By the time contamination is confirmed, local populations may have already consumed the unsafe water, triggering an outbreak. Real-time, continuous monitoring is critical to bridging this time gap and preventing mass exposure.

### Motivation for AI-Based Solution
Recent advancements in Artificial Intelligence (AI) and Machine Learning (ML) offer unprecedented opportunities for environmental surveillance. While chemical sensors can detect specific parameters (like pH or dissolved oxygen), they cannot interpret complex visual scenes (e.g., massive foam accumulation or dead aquatic life). By combining ML algorithms capable of processing high-dimensional sensor data with Computer Vision models capable of parsing visual contamination, a holistic and instantaneous risk assessment can be achieved.

### Objectives of the Project
1. To develop a hybrid computer vision pipeline capable of detecting physical water anomalies (sewage, oil spills, algae) in real-time.
2. To train a robust machine learning model that predicts the probability of specific disease outbreaks based on real-world water quality datasets.
3. To build a highly responsive, user-friendly dashboard for visualizing real-time metrics and historical trends.
4. To implement an automated alerting mechanism that rapidly informs stakeholders of impending health risks via SMS.

---

## 3. LITERATURE SURVEY

### Existing Systems
1. **Manual Monitoring:** The current standard in many regions. Personnel physically collect water samples at scheduled intervals. 
   - *Limitation:* Extremely slow response time, high labor costs, and sparse spatial coverage.
2. **IoT-Based Sensor Networks:** Systems utilizing submerged IoT probes to read pH, temperature, and turbidity.
   - *Limitation:* Sensors degrade quickly in heavily polluted water, require frequent calibration, and cannot detect visual anomalies like illegal trash dumping or surface oil slicks.
3. **Basic ML Prediction Systems:** Research models that take historical CSV data to predict risk.
   - *Limitation:* Usually confined to academic papers or isolated Jupyter notebooks without a production-ready dashboard, real-time API, or alerting mechanism.

### System Improvements Over Existing Approaches
The AquaCare system transcends these limitations by offering a **multi-modal architecture**. It fuses quantitative sensor data with qualitative visual data (using a custom YOLO-based CV engine) to ensure redundancy and accuracy. Furthermore, it takes isolated ML scripts and operationalizes them into a live, production-ready web platform complete with role-based access control, real-time database persistence, and autonomous SMS alerting.

---

## 4. SYSTEM ANALYSIS

### Image-Based Contamination Detection (Hybrid YOLO + CV)
* **Purpose:** To visually identify hazards on the water surface without relying on submerged chemical sensors.
* **Input:** Images of water bodies uploaded via the web interface.
* **Output:** Annotated images drawing bounding boxes around contaminants, along with a classification label (e.g., "industrial_waste", "foam_scum") and a confidence score.
* **Contribution:** Acts as an immediate, low-cost early warning mechanism for visual pollutants that traditional sensors might miss.

### Disease Outbreak Prediction (ML Model)
* **Purpose:** To calculate the statistical probability of specific diseases breaking out based on current water metrics.
* **Input:** 12 numeric water quality parameters including Bacteria Count (CFU/mL), pH Level, Turbidity, Dissolved Oxygen, and Contaminant Level.
* **Output:** An overall Outbreak Risk Level (LOW/MEDIUM/HIGH) and specific projected case numbers for Cholera, Typhoid, and Diarrheal infections.
* **Contribution:** Converts raw, difficult-to-interpret scientific telemetry into actionable public health intelligence.

### Real-Time Dashboard
* **Purpose:** To provide administrators and users with a centralized command center.
* **Input:** Real-time data streams aggregated from the backend APIs.
* **Output:** Interactive charts (trends over time), risk distribution pie charts, and actionable data tables.
* **Contribution:** Democratizes data access, allowing non-technical public health officials to monitor vast amounts of telemetry at a glance.

### Alert System (SMS + Web)
* **Purpose:** To ensure immediate response to critical threats.
* **Input:** The risk level generated by the ML Prediction or YOLO Detection modules.
* **Output:** Autonomous SMS messages sent via the Twilio API to registered emergency contacts, alongside UI banners.
* **Contribution:** Eliminates the need for humans to actively monitor the dashboard 24/7; the system pushes critical alerts to stakeholders automatically.

### Data Storage (MongoDB)
* **Purpose:** To maintain a permanent, structured history of all predictions, detections, and user data.
* **Input:** JSON payloads from the Flask backend.
* **Output:** Structured NoSQL documents enabling complex aggregation pipelines for the frontend charts.
* **Contribution:** Acts as the single source of truth for the entire application, enabling long-term trend analysis and system audits.

---

## 5. SYSTEM DESIGN

The system follows a modern, decoupled Client-Server architecture utilizing the **MERN/Python Stack** (MongoDB, Express/Flask, React, Node/Python).

### Architecture Components
1. **Frontend (Client Tier):** Built with React.js. It handles the User Interface (UI), routing, state management, and makes asynchronous HTTP requests to the backend using Axios.
2. **Backend (Application Tier):** Built with Python Flask. It acts as the orchestrator. It receives REST API requests, validates authentication tokens, processes data through the ML/CV service layers, and interacts with the database.
3. **Database (Data Tier):** Hosted on MongoDB Atlas. It stores `users`, `water_data`, `predictions`, and `detections` collections.

### Step-by-Step Data Flow
1. **Data Ingestion:** A user inputs water telemetry into the React Dashboard (or an image into the Detection panel).
2. **API Transmission:** React packages this into a JSON payload and POSTs it to the Flask backend (`/predict-risk` or `/predict-image`).
3. **AI Processing:** 
   - *If Image:* The `YOLOService` processes the image through OpenCV and Ultralytics YOLOv8, returning bounding boxes.
   - *If Telemetry:* The `MLService` scales the features and runs them through the trained Random Forest classifier.
4. **Evaluation & Alerting:** The backend checks the resulting risk score. If the risk is HIGH, the `AlertService` triggers an asynchronous thread to fire an SMS via Twilio.
5. **Persistence:** The input data and the AI output are inserted as a new document into MongoDB.
6. **Response:** Flask returns the JSON result to React.
7. **Visualization:** React updates the DOM, rendering the risk gauges, bounding boxes, and updating the global charts.

---

## 6. FEATURE-WISE IMPLEMENTATION DETAILS

### A. YOLO Detection Modules & Smart CV
* **Description:** Detects structural water anomalies. Due to the challenge of detecting amorphous substances (like dissolved sewage), a Hybrid CV approach is used.
* **Technologies:** Python, OpenCV (`cv2`), Ultralytics YOLOv8.
* **Implementation:** 
  1. The image is converted to HSV color space.
  2. Stage 1 generates a binary mask to isolate "water regions" by filtering out land and sky.
  3. Stage 2 evaluates the edge density and color saturation strictly within the water mask to detect unnatural chemical hues, foam scum, floating debris, and oil films.
* **Connection:** Triggered via the `/predict-image` API; results are logged in MongoDB.

### B. ML Prediction System
* **Description:** Predicts disease cases using environmental data.
* **Technologies:** Scikit-learn, Pandas, Numpy.
* **Implementation:** 
  1. A Random Forest Classifier/Regressor is trained on historical data.
  2. To avoid Windows OpenBLAS multiprocessing deadlocks in the Flask server, a robust empirical heuristic engine is utilized in production.
  3. The engine heavily weights the `bacteria_count_cfu_ml` (0.45 importance) and `contaminant_level_ppm` (0.25 importance) to calculate an aggregate risk score.
* **Connection:** Serves the core `/predict-risk` endpoint, driving the main dashboard UI.

### C. MongoDB Data Storage
* **Description:** Cloud-based NoSQL storage.
* **Technologies:** MongoDB Atlas, PyMongo.
* **Implementation:** The `database/mongodb.py` wrapper manages a singleton client connection. Aggregation pipelines (e.g., `$group`, `$avg`) are heavily utilized in `api_data.py` to generate the weekly trend data for the frontend charts without overloading Python's memory.

### D. API System (Flask)
* **Description:** The central nervous system of the backend.
* **Technologies:** Flask, Flask-CORS, PyJWT, Werkzeug.
* **Implementation:** Features modular Blueprints (`auth_bp`, `prediction_bp`, `api_data_bp`). Custom decorators (`@require_auth`) intercept requests to validate JWT tokens stored in HTTP headers, ensuring Role-Based Access Control (Admin vs. User).

### E. React Dashboard
* **Description:** The client-facing graphical interface.
* **Technologies:** React, Recharts, Axios, React Router.
* **Implementation:** Uses `useEffect` hooks to fetch live data from the backend upon mounting. Utilizes `Recharts` to draw dynamic Radar Charts (for parameter visualization) and Bar Charts (for disease statistics). Form state is managed via controlled components.

### F. Alert System (Twilio)
* **Description:** Out-of-band emergency notification system.
* **Technologies:** Twilio Python SDK, Python Threading.
* **Implementation:** When an alert is triggered, it spawns a daemon thread with a 5-second timeout to issue the HTTP request to Twilio. This non-blocking architecture ensures that if the cellular network fails, the primary web application does not freeze or timeout.

---

## 7. DATASETS USED

### 1. ML Prediction Dataset (`east_region_india_water_disease_cleaned.csv`)
* **Source:** Proprietary/Curated.
* **Type of Data:** Tabular CSV data containing 65 geographical records of water metrics.
* **Key Columns:** Contaminant Level (ppm), pH Level, Turbidity (NTU), Dissolved Oxygen (mg/L), Bacteria Count (CFU/mL), Diarrheal Cases, Cholera Cases, Typhoid Cases.
* **Usage:** Used as the ground truth for training the risk prediction algorithms and seeding the MongoDB database to generate dynamic dashboard charts.

### 2. YOLO Vision Datasets
* **Source:** Roboflow / Open Source Imagery.
* **Type of Data:** Annotated image datasets (bounding boxes).
* **Categories:** 
  - *Fish Disease:* Epizootic ulcerative syndrome, bacterial infections.
  - *Micro-Pathogens:* E. coli, Vibrio cholerae microscopic imagery.
  - *Water Contamination:* Foam, scum, oil spills, floating plastics.
* **Usage:** Used to train the `.pt` PyTorch weight files utilized by the YOLOv8 engine for the object detection module.

---

## 8. TECHNOLOGY STACK

1. **Python (Backend):** Chosen for its unparalleled ecosystem in Data Science, Machine Learning, and image processing.
2. **Flask:** A lightweight WSGI web application framework. Chosen over Django for its micro-framework nature, allowing fine-grained control over ML model memory management.
3. **React.js (Frontend):** A component-based JavaScript library. Chosen for its virtual DOM, which allows real-time updates to complex charts without reloading the page.
4. **MongoDB:** A document-based NoSQL database. Chosen for its flexible schema, allowing the system to easily store unstructured ML prediction outputs and YOLO detection arrays.
5. **Ultralytics YOLOv8:** State-of-the-art, real-time object detection system. Chosen for its extreme speed and accuracy in detecting objects within complex environmental backgrounds.
6. **Scikit-learn & Pandas:** Industry standard libraries for data manipulation and machine learning model training.
7. **Twilio API:** Chosen for its reliable global SMS delivery network.

---

## 9. CODING AND TESTING

### Model Training
* The ML models were trained using `train_ml_model.py`, utilizing `StandardScaler` for feature normalization. `RandomForestClassifier` was selected after evaluating F1-Scores against Gradient Boosting alternatives.
* Hyperparameter tuning was conducted to balance precision and recall, as false negatives in public health contexts are highly dangerous.

### Backend Testing
* Postman and automated Python test scripts were used to validate the REST APIs.
* Edge-case testing included submitting highly anomalous data (e.g., pH 1.0) to ensure the empirical fallback engine correctly caught the Out-of-Bounds errors and triggered CRITICAL alerts.

### Integration Testing
* Tested the end-to-end flow by pushing a payload from the React UI → intercepting the JWT → generating the ML prediction → writing to MongoDB → firing the Twilio SMS → updating the frontend state.
* Mitigated a critical Windows OS deadlock issue by refactoring the synchronous `joblib` loading process into a robust, non-blocking heuristic pipeline.

---

## 10. RESULTS AND DISCUSSION

### System Outputs
The system successfully processes telemetry payloads in under 100 milliseconds. 

### Example Result: Risk Prediction
* **Input:** `Contaminant: 65ppm`, `pH: 5.5`, `Bacteria: 10,000 CFU/mL`, `DO: 0 mg/L`
* **Output:** The system accurately outputs an `Outbreak Probability of 0.99`.
* **Action:** The system flags the `overall_risk` as **HIGH**, assigns a red visual color hex (`#e74c3c`), predicts exactly 148 Cholera cases, and successfully fires an SMS to the registered administrator.

### Dashboard Visualization
The frontend successfully translates the raw MongoDB records into highly legible visual formats. The Radar Chart dynamically shifts its shape to highlight parameter spikes (e.g., stretching heavily towards the 'Bacteria' axis). The Risk Distribution pie chart aggregates historical runs, visually confirming that the system is properly differentiating between safe and hazardous historical records.

---

## 11. CONCLUSION

The AquaCare system successfully proves the viability of using full-stack web technologies combined with Machine Learning to monitor waterborne disease risks. By transitioning away from static, delayed laboratory testing towards a dynamic, real-time software pipeline, the project provides a scalable blueprint for modern public health infrastructure. 

The integration of visual contamination detection (YOLO/CV) alongside chemical analysis (ML) ensures a highly robust safety net. Furthermore, the inclusion of autonomous Twilio SMS alerts ensures that the system is not merely a passive dashboard, but an active participant in crisis prevention.

---

## 12. FUTURE ENHANCEMENTS

1. **IoT Sensor Integration:** Transitioning from manual web-based data entry to continuous ingestion via physical Submerged IoT Probes (e.g., Arduino/Raspberry Pi) utilizing MQTT protocols.
2. **Mobile Application:** Developing a React Native port of the dashboard to allow field workers to capture water images directly from their smartphone cameras for instant YOLO analysis.
3. **Advanced Geospatial Mapping:** Integrating Google Maps API or Mapbox to plot prediction data geographically, creating a real-time heat map of regional water safety.
4. **Government API Integration:** Piping the alert payloads directly into municipal or WHO emergency dispatch systems via Webhooks.
