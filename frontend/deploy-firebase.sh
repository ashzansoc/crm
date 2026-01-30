#!/bin/bash

# Build the project for Firebase
npm run build:firebase

# Deploy to Firebase
npx firebase-tools deploy
