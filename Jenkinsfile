pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        stage('Deploy GeoIP Service') {
            steps {

                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'digital_vm',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    ),
                    string(
                        credentialsId: 'digital_SERVER_IP',
                        variable: 'digital_SERVER_IP'
                    ),
                    string(
                        credentialsId: 'geoip_app_dir',
                        variable: 'APP_DIR'
                    )
                ]) {

                    sh '''
                    set -e

                    echo "Connecting to production server..."

                    ssh -i "$SSH_KEY" \
                        -o StrictHostKeyChecking=no \
                        "$SSH_USER@$digital_SERVER_IP" << EOF

                    set -e

                    echo "Deployment directory:"
                    echo "$APP_DIR"

                    cd "$APP_DIR"

                    echo "Current commit:"
                    git log -1 --oneline

                    echo "Fetching latest changes..."
                    git fetch origin

                    echo "Resetting to origin/main..."
                    git reset --hard origin/main

                    echo "Stopping existing containers..."
                    docker compose down

                    echo "Building and starting containers..."
                    docker compose up -d --build

                    echo " Container status:"
                    docker compose ps

                    echo "Deployment completed successfully."


                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Deployment completed successfully'
        }

        failure {
            echo 'Deployment failed'
        }
    }
}
