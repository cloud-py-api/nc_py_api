import { generateRemoteUrl } from '@nextcloud/router'
import { getCurrentUser } from '@nextcloud/auth'
import { davGetClient } from '@nextcloud/files'

const davRequest = `<?xml version="1.0"?>
	<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"
				xmlns:nc="http://nextcloud.org/ns"
				xmlns:ocs="http://open-collaboration-services.org/ns">
		<d:prop>
			<d:getlastmodified />
			<d:getetag />
			<d:getcontenttype />
			<d:resourcetype />
			<oc:fileid />
			<oc:permissions />
			<oc:size />
			<d:getcontentlength />
			<nc:has-preview />
			<oc:favorite />
			<oc:comments-unread />
			<oc:owner-display-name />
			<oc:share-types />
			<nc:contained-folder-count />
			<nc:contained-file-count />
			<nc:acl-list />
			<nc:file-metadata-size />
			<nc:file-metadata-gps />
		</d:prop>
	</d:propfind>`

const requestFileInfo = async (path) => {
	const davClient = davGetClient(generateRemoteUrl(`dav/files/${getCurrentUser().uid}`))
	const response = await davClient.stat(path, {
		details: true,
		data: davRequest,
	})
	return response?.data?.props
}

const formatBytes = (bytes, decimals = 2) => {
	if (bytes === 0) return '0 B'
	const k = 1024
	const dm = decimals < 0 ? 0 : decimals
	const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
	const i = Math.floor(Math.log(bytes) / Math.log(k))
	return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

export {
	requestFileInfo,
	formatBytes,
}
