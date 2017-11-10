				
function connect() {
	  var hostName = "com.google.chrome.example.echo";
	  port = chrome.runtime.connectNative(hostName);
	}
	
function sendMessage(key, val) {
	  message = key + ":" + val;
	  port.postMessage(message);
	}

chrome.webRequest.onHeadersReceived.addListener(
	function(details) {
		for (var i = 0; i < details.responseHeaders.length; ++i) {
			if (details.responseHeaders[i].name === 'Content-Type') {
				 var type = details.responseHeaders[i].value;
				 type.indexOf('text/html');
				if (type.indexOf('text') === -1 && // html, css, javascript 
					type.indexOf('image') === -1 && // png, jpeg, gif
					type.indexOf('font') === -1 && // woff
					type.indexOf('application/javascript') === -1 && 
					type.indexOf('application/x-javascript') === -1 &&
					type.indexOf('application/json') === -1 &&
					type.indexOf('application/x-font-ttf') === -1 &&
					type.indexOf('application/xml') === -1 &&
					type.indexOf('application/x-woff') === -1 &&
					type.indexOf('application/x-shockwave-flash') === -1 &&
					type.indexOf('application/x-www-form-urlencoded') === -1 &&
					type.indexOf('video/x-flv') === -1
					) {
					
					var url = details.url;
					var has_attachment = true;
					var disposition = '';
					
					if (type.indexOf('application/octet-stream') != -1)
					{
						var alowed = false;
						
						for (var i = 0; i < details.responseHeaders.length; ++i) {
							if (details.responseHeaders[i].name === 'Content-Disposition')
							{
								has_attachment = true;
								disposition = details.responseHeaders[i].value;
								alowed = true;
							}
						}
						
						if (alowed = false) {
							var ext = url.split('.').pop();
							if (ext === 'ttf')
								return;
							alert(ext);
							return;
						}
					}
					
					
					if (has_attachment)
					{
						var name = disposition.split('filename').pop();
						name = name.slice(2,-1);
						type = name.split('.').pop();
					}
					else
					{
						var name = url.split('/').pop();
					}
					
					
					connect();
					sendMessage('type', type);
					sendMessage('url', url);
					sendMessage('name', name);

					for (var i = 0; i < details.responseHeaders.length; ++i) {
						if (details.responseHeaders[i].name === 'Content-Length') {
							var size = details.responseHeaders[i].value;
							sendMessage('size', size);
						}
							
						if (details.responseHeaders[i].name === 'Accept-Ranges') {
							var accept_range = details.responseHeaders[i].value;
							if (accept_range === 'bytes')
								sendMessage('resume', 'Yes');
							else
								sendMessage('resume', 'No');
						}
					}		
					
					chrome.tabs.query(
						{
							url: url
						}, 
						function(tab){
							chrome.tabs.remove(tab[0].id);
						}
					);

					return;// {cancel: true};
				}
			}
		}
},
	{
		urls: ["*://*/*"]
	},
	
	["responseHeaders", "blocking"]
);
