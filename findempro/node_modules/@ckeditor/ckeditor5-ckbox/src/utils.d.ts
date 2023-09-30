/**
 * @license Copyright (c) 2003-2023, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see LICENSE.md or https://ckeditor.com/legal/ckeditor-oss-license
 */
/**
 * @module ckbox/utils
 */
import type { InitializedToken } from '@ckeditor/ckeditor5-cloud-services';
/**
 * Creates URLs for the image:
 * - responsive URLs for the "webp" image format,
 * - one fallback URL for browsers that do not support the "webp" format.
 */
export declare function getImageUrls({ token, id, origin, width, extension }: {
    token: InitializedToken;
    id: string;
    origin: string;
    width: number;
    extension: string;
}): {
    imageFallbackUrl: string;
    imageSources: Array<{
        srcset: string;
        sizes: string;
        type: string;
    }>;
};
/**
 * Returns an environment id from a token used for communication with the CKBox service.
 */
export declare function getEnvironmentId(token: InitializedToken): string;
