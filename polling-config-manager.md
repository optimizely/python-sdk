
## Using the SDK

To use the SDK, the Optimizely instance can be initialized in three different ways as per your requirement.

 1. Initialize Optimizely with a datafile. This datafile will be used as ProjectConfig throughout the life of Optimizely instance.
    ~~~~~~~~~~~~
    optimizely.Optimizely(
      datafile
    )
  
 2. Initialize Optimizely by providing an 'sdk_key'. This will initialize a PollingConfigManager that makes an HTTP GET request to the URL ( formed using your provided sdk key and the default datafile CDN url template) to asynchronously download the project datafile at regular intervals and update ProjectConfig when a new datafile is recieved. A hard-coded datafile can also be provided along with the sdk_key that will be used initially before any update.
    ~~~~~~~~~~~~
    optimizely.Optimizely(
      datafile=None,
      sdk_key='put_your_sdk_key_here'
    )
   
 3. Initialize Optimizely by providing a Config Manager that implements a 'get_config' method.You may use our Polling Config Manager and customize it to your need. 
    ~~~~~~~~~~~~
    optimizely.Optimizely(
      config_manager=custom_config_manager
    )

##### PollingConfigManager

The PollingConfigManager asynchronously polls for datafiles from a specified URL at regular intervals by making HTTP request. 

  polling_config_manager = PollingConfigManager(
                 sdk_key=None,
                 datafile=None,
                 update_interval=None,
                 url=None,
                 url_template=None,
                 logger=None,
                 error_handler=None,
                 notification_center=None,
                 skip_json_validation=False
    )
        
**Note**: One of the sdk_key or url must be provided. When both are provided, url takes the preference.

**sdk_key**
The sdk_key is used to compose the outbound HTTP request to the default datafile location on the Optimizely CDN.

**datafile**
You can provide an initial datafile to bootstrap the  `ProjectConfigManager`  so that it can be used immediately. The initial datafile also serves as a fallback datafile if HTTP connection cannot be established. The initial datafile will be discarded after the first successful datafile poll.

**update_interval**
The update_interval is used to specify a fixed delay in seconds between consecutive HTTP requests for the datafile.

**url_template**
A string with placeholder `{sdk_key}` can be provided so that this template along with the provided sdk key is used to form the target URL.

You may also provide your own logger, error_handler or notification_center. 


###### Advanced configuration
The following properties can be set to override the default configurations for PollingConfigManager.

| **PropertyName** | **Default Value** | **Description**
| -- | -- | --
| update_interval | 5 minutes | Fixed delay between fetches for the datafile 
| sdk_key | None | Optimizely project SDK key
| url | None | URL override location used to specify custom HTTP source for the Optimizely datafile. 
| url_template | 'https://cdn.optimizely.com/datafiles/{sdk_key}.json' | Parameterized datafile URL by SDK key.
| datafile | None | Initial datafile, typically sourced from a local cached source.

A notification signal will be triggered whenever a _new_ datafile is fetched and Project Config is updated. To subscribe to these notifications you can use the `notification_center.add_notification_listener(NotificationTypes.OPTIMIZELY_CONFIG_UPDATE, update_callback)`

  
