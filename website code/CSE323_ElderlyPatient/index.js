// Firebase configuration setup API from my elderly patient monitoring system
const config = {
    apiKey: "AIzaSyDy3IFXNDCgPY5JaZFdldY4yud_9xr1b28",  
    authDomain: "elderly-patient-monitoring.firebaseapp.com",  
    databaseURL: "https://elderly-patient-monitoring-default-rtdb.firebaseio.com",  
    projectId: "elderly-patient-monitoring",  
    storageBucket: "elderly-patient-monitoring.firebasestorage.app", 
    messagingSenderId: "111652178316",  
    appId: "1:111652178316:web:2e74a22da221166b5daea9", 
    measurementId: "G-5RQ3TC88T5" 
};

// Initialize Firebase
firebase.initializeApp(config);
const database = firebase.database();


function loadPatientData() {
    const dataRef = database.ref();

    //real time data using the on function (this will display when new data comes in the database)
    dataRef.on('value', snapshot => {
        const data = snapshot.val();
        console.log("Data fetched:", data);

        if (data) {
            // Access and display each data field directly by using the data in the firebase (look at the file structure of the database)
            document.getElementById("temperature").textContent = `Temperature: ${data.sensorDHT.temperature} °C`;
            document.getElementById("humidity").textContent = `Humidity: ${data.sensorDHT.humidity} %`;
            document.getElementById("body-temp").textContent = `Body Temperature: ${data['Body Temperature']} °F`;
            document.getElementById("fall-status").textContent = `Fall Status: ${data['Fall Status']}`;
            document.getElementById("pulse-sensor").textContent = `Pulse Sensor: ${data['Pulse Status']}`;
        } else {
            console.error("Data not found in the database.");
        }
    }, error => {
        console.error("Error fetching data:", error);
    });
}


window.onload = function() {
    loadPatientData();
};
