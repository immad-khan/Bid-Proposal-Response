FROM elasticsearch:8.11.1

# Add any custom plugins or configurations here
ENV discovery.type=single-node
ENV xpack.security.enabled=false
