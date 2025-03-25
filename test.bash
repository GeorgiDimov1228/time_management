


# Token Endpoint (Admin Login) with default
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token | json_pp

# Get token and save it to a variable
export TOKEN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin&password=adminpassword" \
http://localhost:8000/api/token | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

# Verify token was captured
echo $TOKEN

# Create a New User
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "rfid": "1234567890",
    "password": "securepassword",
    "is_admin": false
  }' \
  http://localhost:8000/api/users | json_pp

# List All Users
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users | json_pp

# Retrieve a Specific User
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/2 | json_pp

# Update a User
curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "username": "updateduser",
  "email": "updateduser@example.com",
  "rfid": "0987654321",
  "password": "newsecurepassword"
}' \
http://localhost:8000/api/users/1 | json_pp


# Update a User's Password
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "adminpassword",
    "new_password": "newadminpassword"
  }' \
  http://localhost:8000/api/users/1/password | json_pp

# Delete a User
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/users/1 | json_pp

# Attendance Endpoints
curl -X POST "http://localhost:8000/api/checkin?rfid=1234567890" 

# List All Check-In Events
curl http://localhost:8000/api/checkin | json_pp

# Check-Out (Record an Attendance Event)
curl -X POST "http://localhost:8000/api/checkout?rfid=1234567890" | json_pp


# List All Check-Out Events
curl http://localhost:8000/api/checkout | json_pp

curl "http://localhost:8000/api/employees/status?rfid=1234567890" | json_pp

# Now use the token in subsequent requests
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/users" | json_pp

# Test pagination with one user
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/users?skip=0&limit=1" | json_pp

# Test getting non-existent user
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/users/9999" | json_pp



  