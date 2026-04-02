# Agent Sandbox (gVisor) Configuration

This directory contains configuration for running AI agents in a secure sandboxed environment using gVisor.

## Overview

gVisor provides an application kernel that implements a substantial portion of the Linux system call interface, acting as an intermediate layer between applications and the host kernel. This provides:

- **System Call Isolation**: Agents can only access approved system calls
- **File System Restrictions**: Limited file system access to designated directories
- **Network Controls**: Network access can be restricted or monitored
- **Resource Limits**: CPU, memory, and I/O limits per agent

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Kernel                              │
├─────────────────────────────────────────────────────────────┤
│                      gVisor (runsc)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Sentry    │  │    Gofer    │  │  Host Linux │          │
│  │  (Syscall   │  │  (File      │  │  (Network   │          │
│  │   Handler)  │  │   Access)   │  │   Stack)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    Agent Container                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Customer Success Agent                  │    │
│  │  - OpenAI/Claude SDK                                 │    │
│  │  - Tool Execution                                    │    │
│  │  - MCP Client                                        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Files

- `runsc.toml` - gVisor runtime configuration
- `seccomp.json` - Seccomp security profile
- `capabilities.json` - Linux capabilities configuration
- `network-policy.yaml` - Network access policies
- `k8s-runtime-class.yaml` - Kubernetes RuntimeClass for gVisor

## Usage

### Local Development

```bash
# Run container with gVisor
docker run --runtime=runsc \
  --name=agent-sandbox \
  customer-success-fte:latest
```

### Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: agent-pod
spec:
  runtimeClassName: gvisor
  containers:
  - name: agent
    image: customer-success-fte:latest
```

## Security Considerations

1. **Never run as root**: Agents should run as unprivileged users
2. **Read-only root filesystem**: Use volumes for writable paths
3. **Drop all capabilities**: Only add back what's absolutely needed
4. **Network policies**: Restrict egress to required endpoints only
5. **Resource quotas**: Set CPU/memory limits to prevent DoS
