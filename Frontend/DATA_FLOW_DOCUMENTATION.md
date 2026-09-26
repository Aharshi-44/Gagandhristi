# Complete Data Flow: User Input → Frontend → Backend → Database

This document explains how data flows through the GARUDA application, from user input in the UI to final storage in the database, including the role of frontend data models.

## Overview

The application follows a 4-step project configuration process:
1. **Step 1**: Basic Project Info (name, description, auxData)
2. **Step 2**: Add Users with Roles
3. **Step 3**: Define Areas of Interest (AOIs)
4. **Step 4**: Configure Subscriptions (alert channels)

---

## 📊 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT (Vue Components)                  │
│  Step1BasicInfo.vue │ Step2AddUsers.vue │ Step3DefineAOI.vue   │
│  Step4Subscriptions.vue                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              ProjectFormData (Form State Management)            │
│  • Stores: users[], aoiDrafts[], subscriptions[], auxDataDrafts│
│  • Methods: addAOIDraft(), removeUser(), addOrUpdateSubscription│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            ProjectStore (Pinia Store - State Management)        │
│  submitProject() → projectForm.toBackendBundle()               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         FRONTEND MODELS (Data Structure Blueprints)             │
│  ProjectBundleModel → aggregates all models                     │
│    ├─ ProjectModel (projectName, description, auxData)         │
│    ├─ UserProjectModel[] (userId, roles)                       │
│    ├─ AreaOfInterestModel[] (geometry, properties, auxData)    │
│    └─ SubscriptionModel[] (channelId, userIds, status)         │
│                                                                 │
│  toBackendBundle() converts form data to backend format        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ HTTP POST /api/projects
┌─────────────────────────────────────────────────────────────────┐
│              ApiClient (HTTP Communication)                     │
│  api.createProject(bundle) → axios.post('/projects', bundle)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           BACKEND: ProjectController (HTTP Handler)             │
│  POST /api/projects                                             │
│  • Extracts bundle from req.body                                │
│  • Calls projectService.createProject(bundle, currentUserId)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          BACKEND: ProjectService (Business Logic)               │
│  • Validates bundle structure                                   │
│  • Creates database transaction                                 │
│  • Processes: Project → Users → AOIs → Subscriptions           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         BACKEND MODELS (Database Abstraction)                   │
│  • ProjectModel.save() → INSERT INTO project                    │
│  • UsersToProjectModel.save() → INSERT INTO users_to_project   │
│  • AreaOfInterestModel.save() → INSERT INTO area_of_interest    │
│  • SubscriptionModel.save() → INSERT INTO subscription          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL DATABASE                          │
│  Tables: project, users_to_project, area_of_interest,          │
│          subscription, alert_channel_catalogue                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Step-by-Step Detailed Flow

### **PHASE 1: User Input (Frontend Components)**

#### Files Involved:
- `src/components/steps/Step1BasicInfo.vue`
- `src/components/steps/Step2AddUsers.vue`
- `src/components/steps/Step3DefineAOI.vue`
- `src/components/steps/Step4Subscriptions.vue`
- `src/views/ConfigureProjectUI.vue`

#### What Happens:
1. User enters project name, description in Step 1
2. User adds users with roles in Step 2
3. User draws AOIs on map in Step 3
4. User configures subscriptions in Step 4

#### Data Structure at this Stage:
```javascript
// Stored in ProjectFormData instance
{
  projectName: "My Project",
  description: "Project description",
  auxDataDrafts: [{key: "key1", value: "value1"}],
  users: [
    {userId: "user1", roles: [1, 2]},
    {userId: "user2", roles: [3]}
  ],
  aoiDrafts: [AreaOfInterestDraft instances],
  subscriptions: [
    {
      aoiId: "aoi_1",
      clientAoiId: 1,
      channelId: 5,
      userIds: ["user1", "user2"],
      status: 1
    }
  ]
}
```

---

### **PHASE 2: Form State Management (ProjectFormData)**

#### File: `src/classes/ProjectFormData.js`

#### What It Does:
- Manages the volatile form state during the 4-step process
- Provides methods to manipulate form data:
  - `addAOIDraft(aoi)` - Add an AOI
  - `removeUser(userId)` - Remove user and clean up subscriptions
  - `addOrUpdateSubscription(...)` - Manage subscriptions
  - `toBackendBundle()` - **Key Method**: Converts form data to backend format

#### Key Method: `toBackendBundle()`
```javascript
toBackendBundle() {
    // 1. Convert auxDataDrafts to object
    const finalAuxData = this.getFinalAuxData();
    
    // 2. Update bundle's project model
    this.bundle.project.projectName = this.projectName;
    this.bundle.project.description = this.description;
    this.bundle.project.auxData = finalAuxData;
    
    // 3. Convert users to UserProjectModel instances
    this.bundle.users = this.users.map(u => UserProjectModel.fromFormData(u));
    
    // 4. Convert AOI drafts to AreaOfInterestModel instances
    this.bundle.aois = this.aoiDrafts.map(draft => AreaOfInterestModel.fromDraft(draft));
    
    // 5. Convert subscriptions to SubscriptionModel instances
    this.bundle.subscriptions = this.subscriptions.map(sub => new SubscriptionModel(sub));
    
    // 6. Return the complete bundle via ProjectBundleModel.toBackendBundle()
    return this.bundle.toBackendBundle();
}
```

---

### **PHASE 3: Frontend Models (Data Structure Blueprints)**

#### Files:
- `src/models/ProjectModel.js`
- `src/models/UserProjectModel.js`
- `src/models/AreaOfInterestModel.js`
- `src/models/SubscriptionModel.js`
- `src/models/ProjectBundleModel.js`

#### What Frontend Models Do:

**1. Act as Blueprints**: Define the exact structure of data that will be sent to backend

**2. Provide Validation**: Each model has a `validate()` method
```javascript
// Example from ProjectModel
validate() {
    const errors = [];
    if (!this.projectName || this.projectName.trim() === '') {
        errors.push('Project name is required');
    }
    return { valid: errors.length === 0, errors };
}
```

**3. Convert to Backend Format**: `toBackendBundle()` methods format data correctly
```javascript
// ProjectBundleModel.toBackendBundle()
return {
    projectBasicInfo: this.project.toBackendBundle(), // {projectName, description, auxData}
    userData: this.users.map(u => u.toBackendBundle()), // [{userId, roles}]
    aoiData: this.aois.map(a => a.toBackendBundle()), // [{aoiId, name, geomGeoJson, ...}]
    subscriptionData: this.subscriptions.map(s => s.toBackendBundle()) // [{aoiId, channelId, userIds, ...}]
}
```

**4. Provide Utility Methods**: 
- `SubscriptionModel.hasUser(userId)` - Check if user is subscribed
- `UserProjectModel.hasRole(role)` - Check user roles
- `AreaOfInterestModel.validate()` - Validate geometry

---

### **PHASE 4: Store & Submission (ProjectStore)**

#### File: `src/stores/ProjectStore.js`

#### What Happens:
1. User clicks "Submit" in `ConfigureProjectUI.vue`
2. `handleSubmit()` is called
3. Calls `projectStore.submitProject()`

#### Code Flow:
```javascript
// In ProjectStore.js
async function submitProject() {
    // 1. Convert form data to backend bundle format
    const bundle = projectForm.value.toBackendBundle();
    
    // 2. Send to backend via API
    if (projectForm.value.isUpdateMode) {
        response = await api.updateProject(projectForm.value.projectIdToUpdate, bundle);
    } else {
        response = await api.createProject(bundle); // ← HTTP POST
    }
    
    // 3. Reset form on success
    projectForm.value.reset();
}
```

---

### **PHASE 5: API Communication**

#### File: `src/api/backendAPIendpoint.js`

#### What Happens:
```javascript
// ApiClient.createProject(bundle)
async createProject(bundle) {
    // Sends HTTP POST request to /api/projects
    // bundle structure matches what ProjectBundleModel.toBackendBundle() returns
    return this.client.post('/projects', bundle);
}
```

#### Bundle Structure Sent to Backend:
```json
{
  "projectBasicInfo": {
    "projectName": "My Project",
    "description": "Description",
    "auxData": {"key1": "value1"}
  },
  "userData": [
    {"userId": "user1", "roles": [1, 2]},
    {"userId": "user2", "roles": [3]}
  ],
  "aoiData": [
    {
      "aoiId": "aoi_1",
      "name": "AOI 1",
      "geomGeoJson": {"type": "Polygon", "coordinates": [...]},
      "geomProperties": {...},
      "auxData": null
    }
  ],
  "subscriptionData": [
    {
      "aoiId": "aoi_1",
      "channelId": 5,
      "userIds": ["user1", "user2"],
      "alertDisseminationMode": ["notify"],
      "status": 1
    }
  ]
}
```

---

### **PHASE 6: Backend Controller (HTTP Handler)**

#### File: `GARUDA-Backend/src/controllers/ProjectController.js`

#### What Happens:
```javascript
// POST /api/projects
createProject = async (req, res) => {
    const currentUserId = req.header('X-User-ID');
    const projectBundle = req.body; // ← Receives the bundle from frontend
    
    try {
        // Pass bundle to service layer
        const newProject = await this.projectService.createProject(
            projectBundle, 
            currentUserId
        );
        
        return res.status(201).json({
            message: 'Project created successfully.',
            project: newProject
        });
    } catch (error) {
        return res.status(500).json({
            error: 'Failed to create project.',
            details: error.message
        });
    }
}
```

---

### **PHASE 7: Backend Service (Business Logic)**

#### File: `GARUDA-Backend/src/services/ProjectService.js`

#### What Happens:
```javascript
async createProject(bundle, currentUserId) {
    const client = await db.pool.connect();
    try {
        await client.query('BEGIN'); // Start transaction
        
        // 1. Extract project info
        const { projectName, description, auxData } = bundle.projectBasicInfo;
        
        // 2. Validate all AOIs have subscriptions
        // ... validation logic ...
        
        // 3. INSERT INTO project table
        const projectResult = await client.query(`
            INSERT INTO project (name, description, created_by_userid, auxdata)
            VALUES ($1, $2, $3, $4)
            RETURNING id, creation_timestamp;
        `, [projectName, description, currentUserId, auxData]);
        
        const projectId = projectResult.rows[0].id;
        
        // 4. INSERT users into users_to_project table
        for (const user of bundle.userData) {
            const model = new UsersToProjectModel({
                user_id: user.userId,
                project_id: projectId,
                user_role: user.roles
            });
            await model.save(client); // ← Uses backend model
        }
        
        // 5. INSERT AOIs into area_of_interest table
        for (const aoiItem of bundle.aoiData) {
            // Convert GeoJSON to PostGIS geometry
            await client.query(`
                INSERT INTO area_of_interest 
                (project_id, aoi_id, name, geom, auxdata, status)
                VALUES ($1, $2, $3, ST_GeomFromGeoJSON($4), $5, 1)
            `, [projectId, aoiItem.aoiId, aoiItem.name, 
                JSON.stringify(aoiItem.geomGeoJson), aoiItem.auxData]);
        }
        
        // 6. INSERT subscriptions into subscription table
        for (const sub of bundle.subscriptionData) {
            if (sub.status !== 2) { // Skip deleted
                const subscription = new SubscriptionModel({
                    project_id: projectId,
                    aoi_id: sub.aoiId,
                    channel_id: sub.channelId,
                    user_ids: sub.userIds,
                    alert_dissemination_mode: sub.alertDisseminationMode,
                    auxdata: sub.auxData,
                    status: sub.status
                });
                await subscription.save(client); // ← Uses backend model
            }
        }
        
        await client.query('COMMIT'); // Commit transaction
        return newProject;
        
    } catch (error) {
        await client.query('ROLLBACK'); // Rollback on error
        throw error;
    } finally {
        client.release();
    }
}
```

---

### **PHASE 8: Backend Models (Database Abstraction)**

#### Files:
- `GARUDA-Backend/src/models/ProjectModel.js`
- `GARUDA-Backend/src/models/UsersToProjectModel.js`
- `GARUDA-Backend/src/models/AreaOfInterestModel.js`
- `GARUDA-Backend/src/models/SubscriptionModel.js`

#### What Backend Models Do:
- **Abstract database operations**: Handle SQL queries
- **Map database columns**: Convert between DB format and JavaScript objects
- **Provide save/update methods**: Encapsulate INSERT/UPDATE logic

#### Example: SubscriptionModel.save()
```javascript
async save(client) {
    const query = `
        INSERT INTO subscription
        (project_id, aoi_id, channel_id, user_ids, alert_dissemination_mode, auxdata, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id;
    `;
    const values = [
        this.projectId,
        this.aoiId,
        this.channelId,
        this.userIds, // PostgreSQL array
        this.alertDisseminationMode,
        this.auxData,
        this.status
    ];
    
    const result = await client.query(query, values);
    this.id = result.rows[0].id; // Store returned ID
    return this.id;
}
```

---

### **PHASE 9: Database Storage**

#### PostgreSQL Tables:

1. **`project`** table
   - `id` (SERIAL PRIMARY KEY)
   - `name` (VARCHAR)
   - `description` (TEXT)
   - `created_by_userid` (VARCHAR)
   - `auxdata` (JSONB)
   - `creation_timestamp` (TIMESTAMP)

2. **`users_to_project`** table
   - `id` (SERIAL PRIMARY KEY)
   - `user_id` (VARCHAR)
   - `project_id` (INTEGER)
   - `user_role` (INTEGER[]) - Array of role IDs

3. **`area_of_interest`** table
   - `id` (SERIAL PRIMARY KEY)
   - `project_id` (INTEGER)
   - `aoi_id` (VARCHAR)
   - `name` (VARCHAR)
   - `geom` (GEOMETRY) - PostGIS geometry
   - `auxdata` (JSONB)
   - `status` (INTEGER)

4. **`subscription`** table
   - `id` (SERIAL PRIMARY KEY)
   - `project_id` (INTEGER)
   - `aoi_id` (VARCHAR)
   - `channel_id` (INTEGER)
   - `user_ids` (VARCHAR[]) - Array of user IDs
   - `alert_dissemination_mode` (VARCHAR[])
   - `auxdata` (JSONB)
   - `status` (INTEGER)

---

## 🔄 Reverse Flow: Database → Frontend (Reading Data)

### Flow for Loading/Updating a Project:

1. **Frontend**: `projectStore.loadProjectForUpdate(projectId)`
2. **API Call**: `api.getProjectDetails(projectId)` → GET `/api/projects/:id`
3. **Backend Controller**: `ProjectController.getProjectDetails()`
4. **Backend Service**: `ProjectService.getProjectDetails(projectId)`
   - Queries database using backend models
   - Joins tables to get complete project data
   - Returns structured JSON
5. **Frontend Store**: `mapBackendToForm(data)`
   - Converts backend JSON to `ProjectFormData`
   - Uses `ProjectBundleModel.fromBackend()` to create model instances
   - Converts models back to form-friendly format (drafts)
6. **Components**: Display data in form for editing

---

## 🎯 Key Differences: Frontend vs Backend Models

### **Frontend Models** (`src/models/`)
- **Purpose**: Blueprint for data structure sent to backend
- **No Database Access**: Don't interact with database
- **Client-Side Validation**: Validate before sending to backend
- **Format Conversion**: Convert form data to backend-compatible format
- **Examples**: 
  - `ProjectModel.toBackendBundle()` returns `{projectName, description, auxData}`
  - `SubscriptionModel.toBackendBundle()` formats subscription data

### **Backend Models** (`GARUDA-Backend/src/models/`)
- **Purpose**: Database abstraction layer
- **Database Access**: Execute SQL queries via DBClient
- **Data Persistence**: Save/update/delete in database
- **Database Mapping**: Map between DB columns and JavaScript objects
- **Examples**:
  - `ProjectModel.save()` executes `INSERT INTO project`
  - `SubscriptionModel.findByProjectId()` executes `SELECT FROM subscription`

---

## 📝 Summary: What Frontend Models Do

1. **Define Data Structure**: Act as contracts for what data looks like
2. **Validate Before Sending**: Ensure data is valid before API calls
3. **Format Conversion**: Transform form data (drafts) to backend format
4. **Type Safety**: Provide clear structure for TypeScript/JSDoc
5. **Reduce Complexity**: Encapsulate conversion logic away from components
6. **Enable Reusability**: Can be used across different parts of the app

---

## 🚀 Example: Complete Flow for Adding a Subscription

```
1. USER ACTION (Step4Subscriptions.vue)
   User clicks "Add Subscription" button
   → Calls saveSubscriptionFromModal()

2. FORM UPDATE (ProjectFormData)
   props.projectData.addOrUpdateSubscription(
       clientAoiId, channelId, userIds
   )
   → Adds to form.subscriptions array

3. SUBMISSION (ProjectStore)
   User clicks "Submit Project"
   → projectForm.toBackendBundle()

4. MODEL CONVERSION (ProjectBundleModel)
   this.subscriptions.map(sub => new SubscriptionModel(sub))
   → Creates SubscriptionModel instances
   → subscription.toBackendBundle() formats data

5. API CALL (ApiClient)
   api.createProject(bundle)
   → POST /api/projects with bundle.subscriptionData

6. BACKEND CONTROLLER
   ProjectController.createProject()
   → Receives bundle, calls service

7. BACKEND SERVICE
   ProjectService.createProject()
   → For each subscription in bundle.subscriptionData:
       new SubscriptionModel({...})
       await subscription.save(client)

8. BACKEND MODEL
   SubscriptionModel.save()
   → INSERT INTO subscription VALUES (...)

9. DATABASE
   Data stored in subscription table
```

---

## 🔗 File Reference Map

### Frontend Files:
- **Components**: `src/components/steps/*.vue`
- **Form Management**: `src/classes/ProjectFormData.js`
- **State Store**: `src/stores/ProjectStore.js`
- **Models**: `src/models/*.js`
- **API Client**: `src/api/backendAPIendpoint.js`

### Backend Files:
- **Controller**: `GARUDA-Backend/src/controllers/ProjectController.js`
- **Service**: `GARUDA-Backend/src/services/ProjectService.js`
- **Models**: `GARUDA-Backend/src/models/*.js`
- **Database**: `GARUDA-Backend/src/db/DBClient.js`

---

This architecture ensures:
✅ **Separation of Concerns**: Each layer has a specific responsibility
✅ **Data Validation**: Frontend validates before sending, backend validates before saving
✅ **Type Safety**: Models define clear contracts
✅ **Maintainability**: Changes to data structure are localized to models
✅ **Testability**: Each layer can be tested independently


