# needed --platform=linux/amd64 due Mac M1's Chips
FROM --platform=linux/amd64 nginx


# Copy custom Nginx configuration
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY entrypoint.sh /home/entrypoint.sh
# Expose the ports for Nginx
EXPOSE 80

RUN chmod +x /home/entrypoint.sh

# Start Nginx
ENTRYPOINT ["/home/entrypoint.sh"]
