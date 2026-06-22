
/**
 * Glaaster plugin JavaScript for adding file links to Moodle course pages.
 * Adds Glaaster buttons to supported file types in resource and folder modules.
 *
 * @module      mod_glaaster/before_footer
 * @package     mod_glaaster
 * @copyright   2025 Glaaster
 * @license     http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
(function(){'use strict';const SUPPORTEDFILEEXTENSIONS=['.pdf','.png','.jpeg','.jpg','.docx','.pptx','.odt','.odp'];const SUPPORTEDEXTS=new Set(SUPPORTEDFILEEXTENSIONS);const SUPPORTEDFILEICONS=['f/pdf','f/image','f/document','f/powerpoint','f/writer','f/impress'];function warn(...args){try{console.warn('Glaaster WARN:',...args)}catch(e){}}
function safeBtoa(str){try{return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,function(match,p1){return String.fromCharCode('0x'+p1)}))}catch(e){warn('Unable to base64-encode string',str,e);return''}}
function hasSupportedExtension(text){if(!text){return!1}
const lower=text.toLowerCase();for(const ext of SUPPORTEDEXTS){if(lower.includes(ext)){return!0}}
return!1}
function hasSupportedFileIcon(src){if(!src){return!1}
return SUPPORTEDFILEICONS.some(icon=>src.includes(icon))}
function hasGlaasterLink(container){return!!(container&&container.querySelector('a[data-glaaster-link="true"]'))}
function createGlaasterLink(url,title,imgClass){const a=document.createElement('a');a.setAttribute('data-glaaster-link','true');a.href=url;a.title=title||'';const klass=(imgClass||'').toString().trim();a.innerHTML=`<img src="${M.cfg.wwwroot}/mod/glaaster/pix/icon.svg" class="${klass}" `+`alt="${title || ''}" role="presentation" aria-hidden="true">`;return a}
function buildGlaasterUrl(params){const base=`${M.cfg.wwwroot}/mod/glaaster/view.php`;const usp=new URLSearchParams(params);return `${base}?${usp.toString()}`}
function extractIdFromHref(href){try{const u=new URL(href,window.location.origin);return u.searchParams.get('id')}catch(e){const m=href&&href.match(/(?:\?|&)id=(\d+)/);return m?m[1]:null}}
function extractPluginFilePath(href){if(!href){return null}
const re=/\/pluginfile\.php\/[^/]+\/mod_folder\/content\/[^/]+\/(.*)$/;const m=href.match(re);if(!m||!m[1]){return null}
const raw=m[1].split('?')[0];try{return decodeURIComponent(raw)}catch(e){return raw}}
function addGlaasterButtonsToFiles(fileLinks,folderModuleId,translation){fileLinks.forEach((fileAnchor)=>{try{const fileLabel=(fileAnchor.textContent||'').trim();if(!hasSupportedExtension(fileLabel)){return}
const extractedPath=extractPluginFilePath(fileAnchor.getAttribute('href'));const fullFilePath=extractedPath||fileLabel;const parts=fullFilePath.split('/').filter(Boolean);const fileBaseName=parts.pop()||fullFilePath;const fileDir=parts.length?`/${parts.join('/')}/`:'/';const parent=fileAnchor.parentNode||fileAnchor;if(hasGlaasterLink(parent)){return}
const url=buildGlaasterUrl({l:String(glaasterInstanceId),course_module_id:String(folderModuleId),file_name:safeBtoa(fileBaseName),file_path:safeBtoa(fileDir)});parent.appendChild(createGlaasterLink(url,translation,'icon'))}catch(e){warn('Failed adding folder file link',e)}})}
document.addEventListener('DOMContentLoaded',function(){if(typeof M==='undefined'||!M.cfg||!M.cfg.wwwroot){warn('Moodle config not available (M.cfg.wwwroot). Aborting.');return}
const hasInstance=typeof glaasterInstanceId!=='undefined'&&!!glaasterInstanceId;if(typeof window.require!=='function'){warn('Moodle AMD loader (require) not found. Aborting.');return}
window.require(['core/str'],function(str){str.get_string('view_document_adaptive','mod_glaaster').done(function(translation){if(!hasInstance){warn('glaasterInstanceId is undefined/empty. Skipping link injection.');return}
const resources=document.querySelectorAll('li.modtype_resource, li.modtype_page');resources.forEach((resource)=>{try{const activityLink=resource.querySelector('div.activityname a, .activityname .aalink');if(!activityLink){return}
const href=activityLink.getAttribute('href');const resourceId=extractIdFromHref(href);if(!resourceId){return}
let activityContainer=resource.querySelector('.activity-grid');if(!activityContainer){return}
const img=activityContainer?activityContainer.querySelector('img'):null;const isSupported=img&&hasSupportedFileIcon(img.src);if(isSupported&&activityContainer&&!hasGlaasterLink(activityContainer)){const url=buildGlaasterUrl({l:String(glaasterInstanceId),course_module_id:String(resourceId)});activityContainer.prepend(createGlaasterLink(url,translation,'activityicon'))}}catch(e){warn('Failed processing a resource element',e)}});const folders=document.querySelectorAll('li.modtype_folder');folders.forEach((folderLi)=>{const folderModuleId=folderLi.getAttribute('data-id');if(!folderModuleId){return}
const fileLinks=folderLi.querySelectorAll('span.fp-filename a');if(fileLinks.length){addGlaasterButtonsToFiles(fileLinks,folderModuleId,translation)}});if(window.location.pathname.includes('/mod/folder/view.php')){const urlParams=new URLSearchParams(window.location.search);const folderModuleId=urlParams.get('id');if(folderModuleId){const fileLinks=document.querySelectorAll('.fp-filename a');if(fileLinks.length){addGlaasterButtonsToFiles(fileLinks,folderModuleId,translation)}}}})})})})()