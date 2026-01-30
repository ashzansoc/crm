// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBVTHBeu7QUIua4HmWAm8rFjssDK-YkJf4",
  authDomain: "ashutosh-a2720.firebaseapp.com",
  projectId: "ashutosh-a2720",
  storageBucket: "ashutosh-a2720.firebasestorage.app",
  messagingSenderId: "302526843375",
  appId: "1:302526843375:web:e39ec25b7d217336e50e1a",
  measurementId: "G-Q211FHGJWP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export { app, analytics };
