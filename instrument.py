from newrelic.agent import (background_task, function_trace,
        add_custom_parameter, wrap_function_trace, BackgroundTaskWrapper,
        wrap_function_wrapper, current_transaction, ExternalTrace,
        FunctionTraceWrapper)

def wrapper_register_ip(wrapped, instance, args, kwargs):
    def _bind_params(domain, hostname, ipaddr):
        return domain, hostname, ipaddr

    domain, hostname, ipaddr = _bind_params(*args, **kwargs)

    add_custom_parameter('domain', domain)
    add_custom_parameter('hostname', hostname)
    add_custom_parameter('ipaddr', ipaddr)

    return wrapped(*args, **kwargs)

def instrument_dyndns53(module):
    wrap_function_trace(module, 'initialise_database')
    wrap_function_trace(module, 'download_database')
    wrap_function_trace(module, 'upload_database')

    wrap_function_trace(module, 'register_ip')

    wrap_function_trace(module, 'BasicAuthDatabase.check_credentials')

    wrap_function_wrapper(module, 'register_ip', wrapper_register_ip)

    for name, callback in list(module._commands.items()):
        module._commands[name] = BackgroundTaskWrapper(callback)

def wrap_object_function_traces(obj, names):
    for name in names:
        setattr(obj, name, FunctionTraceWrapper(getattr(obj, name)))

def wrapper_AWSAuthConnection_make_request(wrapped, instance, args, kwargs):
    transaction = current_transaction()

    if transaction is None:
        return wrapped(*args, **kwargs)

    def _bind_params(method, path, *args, **kwargs):
        return method, path

    method, path = _bind_params(*args, **kwargs)

    url = '%s://%s%s' % (instance.protocol, instance.host, path)

    with ExternalTrace(transaction, 'boto', url, method):
        return wrapped(*args, **kwargs)

def instrument_boto_connection(module):
    wrap_function_wrapper(module, 'AWSAuthConnection.make_request',
            wrapper_AWSAuthConnection_make_request)

def instrument_boto_route53_connection(module):
    wrap_object_function_traces(module.Route53Connection,
	    ['get_all_hosted_zones', 'get_hosted_zone',
	    'get_hosted_zone_by_name', 'create_hosted_zone',
	    'delete_hosted_zone', 'get_all_rrsets', 'change_rrsets',
	    'get_change', 'create_zone', 'get_zone', 'get_zones'])

def instrument_boto_s3_bucket(module):
    wrap_object_function_traces(module.Bucket,
	    ['get_key', 'list', 'list_versions', 'list_multipart_uploads',
	    'get_all_keys', 'get_all_versions', 'get_all_multipart_uploads',
            'new_key', 'delete_keys', 'delete_key', 'copy_key',
            'set_canned_acl', 'get_xml_acl', 'set_xml_acl', 'set_acl',
            'get_acl', 'set_subresource', 'get_subresource', 'make_public',
            'add_email_grant', 'add_user_grant', 'list_grants',
            'get_location', 'set_xml_logging', 'enable_logging',
            'disable_logging', 'get_logging_status', 'set_as_logging_target',
            'get_request_payment', 'set_request_payment',
            'configure_versioning', 'get_versioning_status',
            'configure_lifecycle', 'get_lifecycle_config',
            'delete_lifecycle_configuration', 'configure_website',
            'set_website_configuration', 'set_website_configuration_xml',
            'get_website_configuration', 'get_website_configuration_obj',
            'get_website_configuration_with_xml',
            'get_website_configuration_xml',
            'delete_website_configuration', 'get_website_endpoint',
            'get_policy', 'set_policy', 'delete_policy', 'set_cors_xml',
            'set_cors', 'get_cors_xml', 'get_cors', 'delete_cors',
            'initiate_multipart_upload', 'complete_multipart_upload',
            'cancel_multipart_upload', 'delete', 'get_tags', 'get_xml_tags',
            'set_xml_tags', 'set_tags', 'delete_tags'])

def instrument_boto_s3_connection(module):
    wrap_object_function_traces(module.S3Connection,
            ['get_all_buckets', 'get_canonical_user_id', 'get_bucket',
            'lookup', 'create_bucket', 'delete_bucket'])

def instrument_boto_s3_key(module):
    wrap_object_function_traces(module.Key,
            ['open_read', 'open', 'close', 'change_storage_class', 'copy',
            'exists', 'delete', 'set_acl', 'get_acl', 'get_xml_acl',
            'set_xml_acl', 'set_canned_acl', 'get_redirect',
            'set_redirect', 'make_public', 'send_file',
            'set_contents_from_stream', 'set_contents_from_file',
            'set_contents_from_filename', 'set_contents_from_string',
            'get_file', 'get_torrent_file', 'get_contents_to_file',
            'get_contents_to_filename', 'get_contents_as_string',
            'add_email_grant', 'add_user_grant', 'set_remote_metadata',
            'restore'])

def instrument_boto(module):
    wrap_object_function_traces(module, ['connect_s3', 'connect_route53'])
