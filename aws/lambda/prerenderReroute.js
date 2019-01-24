// https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/prerenderReroute/versions/1?tab=graph
// arn:aws:lambda:us-east-1:306439459454:function:prerenderReroute:1
exports.handler = (event, context, callback) => {
  const request = event.Records[0].cf.request;
  if (request.headers['x-prerender-token'] && request.headers['x-prerender-host']) {
    request.origin = {
      custom: {
        domainName: 'service.prerender.io',
        port: 443,
        protocol: 'https',
        readTimeout: 20,
        keepaliveTimeout: 5,
        customHeaders: {},
        sslProtocols: ['TLSv1', 'TLSv1.1'],
        path: '/https%3A%2F%2F' + request.headers['x-prerender-host'][0].value
      }
    };
  }
  callback(null, request);
};
