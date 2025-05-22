#!/bin/bash

# Function to prompt for input with a default value
prompt_for_input() {
  local var_name="$1"
  local default_value="$2"
  read -p "Enter value for $var_name [$default_value]: " input_value
  echo "${input_value:-$default_value}"
}

# Create .env file
cat <<EOL > .env
POSTGRES_USER=$(prompt_for_input "POSTGRES_USER" "yourusername")
POSTGRES_PASSWORD=$(prompt_for_input "POSTGRES_PASSWORD" "yourpassword")
DATABASE_URL=postgresql://$(prompt_for_input "POSTGRES_USER" "yourusername"):$(prompt_for_input "POSTGRES_PASSWORD" "yourpassword")@db:5432/time_management_db
SECRET_KEY=$(prompt_for_input "SECRET_KEY" "86ecf38ce7746630f10bb0cfcfee6be1bc4f037dd7f84c5799b009a803dac2q5")
ALGORITHM=$(prompt_for_input "ALGORITHM" "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=$(prompt_for_input "ACCESS_TOKEN_EXPIRE_MINUTES" "30")
DEFAULT_ADMIN_USERNAME=$(prompt_for_input "DEFAULT_ADMIN_USERNAME" "admin")
DEFAULT_ADMIN_EMAIL=$(prompt_for_input "DEFAULT_ADMIN_EMAIL" "admin@example.com")
DEFAULT_ADMIN_PASSWORD=$(prompt_for_input "DEFAULT_ADMIN_PASSWORD" "adminpassword")
LISTENER_USERNAME=$(prompt_for_input "LISTENER_USERNAME" "listener")
LISTENER_PASSWORD=$(prompt_for_input "LISTENER_PASSWORD" "listenerpassword")
BRIDGE_USERNAME=$(prompt_for_input "BRIDGE_USERNAME" "bridge")
BRIDGE_PASSWORD=$(prompt_for_input "BRIDGE_PASSWORD" "bridgepassword")
ACTION_COOLDOWN_SECONDS=$(prompt_for_input "ACTION_COOLDOWN_SECONDS" "10")
EOL

echo ".env file created successfully." 