import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

# Load dataset
data = pd.read_excel('student_performance_modified.xlsx')

# Feature Selection (New Features Based on Your Inputs)
X = data[['Gender', 'Age', 'Address', 'Parent Education', 'Travel Time',
          'Study Time', 'Failures', 'Extra Classes', 'Extra Curricular Activities',
          'Internet Access', 'Health', 'Absences', 'Sub1 mark', 'Sub2 mark', 'Sub3 mark']]

# Encode categorical features (if needed)
X = pd.get_dummies(X, drop_first=True)

# Target Values (Final Marks)
y = data[['Sub1 Final Mark', 'Sub2 Final Mark', 'Sub3 Final Mark']]

# Calculate average scores (thresholds for weak subject identification)
thresholds = {
    'Sub1': data['Sub1 Final Mark'].mean(),
    'Sub2': data['Sub2 Final Mark'].mean(),
    'Sub3': data['Sub3 Final Mark'].mean()
}
joblib.dump(thresholds, 'thresholds.pkl')

# Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate Model
y_pred = model.predict(X_test)
print("Model Performance (MSE):", mean_squared_error(y_test, y_pred))

# Save Model
joblib.dump(model, 'student_model.pkl')
