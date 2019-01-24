// https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/addPrerenderRerouteHeaders/versions/1?tab=graph
// arn:aws:lambda:us-east-1:306439459454:function:addPrerenderRerouteHeaders:1
exports.handler = (event, context, callback) => {
  const request = event.Records[0].cf.request;
  const headers = request.headers;
  const user_agent = headers['user-agent'];
  const host = headers['host'];
  if (user_agent && host) {
    let prerender = /bot|googlebot|bingbot|yandex|baiduspider|facebot|facebookexternalhit|twitterbot|rogerbot|linkedinbot|embedly|quora link preview|showyoubot|outbrain|pinterest|slackbot|vkshare|w3c_validator/i.test(user_agent[0].value);
    prerender = prerender || /_escaped_fragment_/.test(request.querystring);
    prerender = prerender && ! /\.(js|css|xml|less|png|jpg|jpeg|gif|pdf|doc|txt|ico|rss|zip|mp3|rar|exe|wmv|doc|avi|ppt|mpg|mpeg|tif|wav|mov|psd|ai|xls|mp4|m4a|swf|dat|dmg|iso|flv|m4v|torrent|ttf|woff|svg|eot|woff2)$/i.test(request.uri);
    if (prerender) {
      headers['x-prerender-token'] = [{ key: 'X-Prerender-Token', value: <PRERENDER_IO_TOKEN>}];
      headers['x-prerender-host'] = [{ key: 'X-Prerender-Host', value: host[0].value}];
      headers['x-prerender-cachebuster'] = [{ key: 'X-Prerender-Cachebuster', value: Date.now().toString()}];
    }
  }
  callback(null, request);
};
