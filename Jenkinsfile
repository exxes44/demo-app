pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        timestamps()
    }
    environment {
        SCANNER_HOME = tool 'sonar-scanner'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup') {
            steps {
                sh 'rm -f result.xml coverage.xml .coverage'
                sh 'python3 -m venv venv'
                sh './venv/bin/pip install --upgrade pip'
                sh './venv/bin/pip install -r requirements.txt'
            }
        }
        stage('Build') {
            steps {
                sh './venv/bin/python -m py_compile app.py'
            }
        }
        stage('Test') {
            steps {
                sh './venv/bin/pytest --junitxml=result.xml --cov=app --cov-report=xml:coverage.xml'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '"$SCANNER_HOME/bin/sonar-scanner"'
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
    post {
        always {
            script {
                if (fileExists('result.xml')) {
                    junit 'result.xml'
                }
            }
        }
        success {
            echo 'Сборка прошла успешно, Quality Gate пройден'
        }
        failure {
            echo 'Сборка завершилась с ошибкой'
        }
    }
}
