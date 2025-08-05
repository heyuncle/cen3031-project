# StrideSync: A Fun Step-Tracking App
StrideSync is a beginner-friendly step-tracking web application designed to encourage daily movement. Users can record steps automatically via fitbit device or enter them manually. The platform visualizes progress through interactive dashboards and leverages community and gamification elements to build lasting habits
## Features & Functionality
- User Authentication
Supports Admin & Member roles to manage permissions & moderate community features
- Step Logging
Syncs automatically with fitbit device sensors or allows manual entry for flexibility
- Database
Persists step history, user profiles, & group data
- Gamification
Awards, points, streaks, & badges to incentivize consistent use
- Community Engagement
Lets users join or create walking groups & compete on leaderboards
- Smart Insights
Displays personalized daily goals & interactive activity graphs

## Architectural Pattern
StrideSync is built on Django’s Model-View-Template (MVT) architecture, ensuring a clean separation of concerns
- Models define the core data structures (steps, groups, badges, users) & handle database interactions
- Views handle the business logic, data aggregation, and API endpoints
- Templates render the user interface, integrating Chart.js for dynamic visualizations of daily, weekly, & monthly data
