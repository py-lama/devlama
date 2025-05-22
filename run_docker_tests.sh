#!/bin/bash

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Create test-reports directory if it doesn't exist
mkdir -p test-reports

print_header() {
    echo -e "\n${BLUE}===========================================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}===========================================================${NC}\n"
}

show_help() {
    echo -e "${YELLOW}PyLama Docker Testing Environment${NC}"
    echo -e "\nUsage: $0 [options]\n"
    echo -e "Options:"
    echo -e "  --build\t\tBuild Docker images before starting"
    echo -e "  --run-tests\t\tRun all tests automatically after starting"
    echo -e "  --interactive\t\tStart in interactive mode (don't run tests automatically)"
    echo -e "  --full-stack\t\tStart all services in the PyLama ecosystem"
    echo -e "  --integration\t\tRun integration tests with all services"
    echo -e "  --ansible-tests\t\tRun Ansible tests"
    echo -e "  --stop\t\tStop and remove containers"
    echo -e "  --clean\t\tStop containers and remove volumes"
    echo -e "  --help\t\tShow this help message"
    echo -e "\nExamples:\n"
    echo -e "  $0 --build --run-tests\t# Build and run all tests"
    echo -e "  $0 --interactive\t\t# Start in interactive mode"
    echo -e "  $0 --full-stack\t\t# Start all services"
    echo -e "  $0 --integration\t\t# Run integration tests"
    echo -e "  $0 --stop\t\t# Stop containers"
}

# Default options
BUILD=false
RUN_TESTS=false
INTERACTIVE=false
FULL_STACK=false
INTEGRATION=false
ANSIBLE_TESTS=false
STOP=false
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --run-tests)
            RUN_TESTS=true
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --full-stack)
            FULL_STACK=true
            shift
            ;;
        --integration)
            INTEGRATION=true
            shift
            ;;
        --ansible-tests)
            ANSIBLE_TESTS=true
            shift
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Stop containers if requested
if [ "$STOP" = true ]; then
    print_header "Stopping Docker containers"
    docker-compose -f docker-compose.test.yml down
    echo -e "${GREEN}Containers stopped${NC}"
    exit 0
fi

# Clean containers and volumes if requested
if [ "$CLEAN" = true ]; then
    print_header "Cleaning Docker containers and volumes"
    docker-compose -f docker-compose.test.yml down -v
    echo -e "${GREEN}Containers and volumes removed${NC}"
    exit 0
fi

# Build and start containers
if [ "$BUILD" = true ]; then
    print_header "Building Docker images"
    docker-compose -f docker-compose.test.yml build
fi

# Start the full stack of services
if [ "$FULL_STACK" = true ]; then
    print_header "Starting full PyLama ecosystem"
    docker-compose -f docker-compose.test.yml up -d pybox-mock pyllm-mock apilama-mock weblama-mock pylama-app
    
    # Wait for the services to be ready
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Check if the main service is running
    SERVICE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
    if [ "$SERVICE_STATUS" = "200" ]; then
        echo -e "${GREEN}PyLama ecosystem is running${NC}"
    else
        echo -e "${RED}Failed to start PyLama ecosystem (status code: $SERVICE_STATUS)${NC}"
        exit 1
    fi
    
    echo -e "\n${YELLOW}Services are running at:${NC}"
    echo -e "  ${GREEN}PyLama:${NC} http://localhost:5000"
    echo -e "  ${GREEN}PyBox:${NC} http://localhost:8001"
    echo -e "  ${GREEN}PyLLM:${NC} http://localhost:8002"
    echo -e "  ${GREEN}APILama:${NC} http://localhost:8080"
    echo -e "  ${GREEN}WebLama:${NC} http://localhost:8081"
    echo -e "\n${YELLOW}To stop the services, run:${NC} $0 --stop"
    exit 0
fi

# Run integration tests if requested
if [ "$INTEGRATION" = true ]; then
    print_header "Running PyLama integration tests"
    docker-compose -f docker-compose.test.yml up pybox-mock pyllm-mock apilama-mock weblama-mock pylama-test
    exit 0
fi

# Run Ansible tests if requested
if [ "$ANSIBLE_TESTS" = true ]; then
    print_header "Running PyLama Ansible tests"
    docker-compose -f docker-compose.test.yml run --rm pylama-test bash -c "cd /app/ansible_tests && ansible-playbook -i inventory/local main_playbook.yml"
    exit 0
fi

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
    print_header "Running PyLama tests"
    docker-compose -f docker-compose.test.yml up pylama-test
    exit 0
fi

# Start interactive mode if requested
if [ "$INTERACTIVE" = true ] || [ "$RUN_TESTS" = false -a "$FULL_STACK" = false -a "$INTEGRATION" = false -a "$ANSIBLE_TESTS" = false ]; then
    print_header "Starting interactive mode"
    echo -e "${YELLOW}Available commands:${NC}"
    echo -e "  ${GREEN}python -m pytest tests/ -v${NC} - Run all tests"
    echo -e "  ${GREEN}python -m pylama.app --port 5000 --host 0.0.0.0${NC} - Start the PyLama service"
    echo -e "  ${GREEN}cd /app/ansible_tests && ansible-playbook -i inventory/local main_playbook.yml${NC} - Run Ansible tests"
    echo -e "\n${YELLOW}Type 'exit' to exit the container${NC}\n"
    
    docker-compose -f docker-compose.test.yml run --rm pylama-test bash
fi

echo -e "\n${YELLOW}To stop the containers, run:${NC} $0 --stop"
echo -e "${YELLOW}To clean up containers and volumes, run:${NC} $0 --clean"
