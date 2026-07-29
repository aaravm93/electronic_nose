import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# Load dataset

data = pd.read_csv(
    "data/samples.csv",
    header=None
)


data.columns = [
        "timestamp",
        "mq3", 
        "mq135", 
        "temp", 
        "humidity", 
        "pressure", 
        "gas_res", 
        "label"
    ]


# Keep only current 3 substances

data = data[data["label"].isin(
    [
        "air",
        "alcohol",
        "coffee",
        "vinegar"
        "asafoetida"
    ]
)]


print("\nSamples per class:")
print(data["label"].value_counts())


features = [
    "mq3",
    "mq135",
    "g200",
    "g250",
    "g300",
    "g320",
    "g350"
]


X = data[features]

y = data["label"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced"
)



model.fit(
    X_train,
    y_train
)


prediction = model.predict(
    X_test
)


print("\nAccuracy:")
print(
    accuracy_score(
        y_test,
        prediction
    )
)


print("\nClassification report:")
print(
    classification_report(
        y_test,
        prediction
    )
)


print("\nConfusion matrix:")
print(
    confusion_matrix(
        y_test,
        prediction
    )
)


scores = cross_val_score(
    model,
    X,
    y,
    cv=5
)


print("\nCross validation scores:")
print(scores)

print(
    "Average CV accuracy:",
    scores.mean()
)


# Feature importance

print("\nFeature importance:")

for name, value in sorted(
    zip(features, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
):
    print(
        name,
        round(value,3)
    )


joblib.dump(
    {
        "model": model,
        "features": features
    },
    "model.joblib"
)


print("\nModel saved as model.joblib")
