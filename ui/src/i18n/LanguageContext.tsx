import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { translateText } from './translations';
import i18n from './config';

export type Locale = 'en' | 'zh-CN';
type LanguageContextValue = { locale: Locale; setLocale: (locale: Locale) => void; t: (text: string) => string; };
const LanguageContext = createContext<LanguageContextValue | null>(null);
const originalText = new WeakMap<Text, string>();
const originalAttributes = new WeakMap<Element, Map<string, string>>();
const extraZhCN: Record<string,string> = {
  'Review Status':'处置状态','Pending review':'待处理','Confirmed issue':'已确认问题','False positive':'误报','Ignored':'已忽略','Resolved':'已解决',
  'Validation':'验证状态','Webhook Template':'Webhook 模板','Custom template':'自定义模板','Default JSON payload':'默认 JSON 数据',
  'Valid JSON. Use placeholders: {{severity}}, {{type}}, {{repository}}, {{file}}, {{line}}, {{description}}, {{commit_hash}}, {{commit_url}}, {{value_preview}}, {{last_seen_at}}.':'必须是有效 JSON，可使用占位符：{{severity}}、{{type}}、{{repository}}、{{file}}、{{line}}、{{description}}、{{commit_hash}}、{{commit_url}}、{{value_preview}}、{{last_seen_at}}。',
  'selected':'已选择','Delete selected findings?':'确定删除选中的发现项吗？','Delete Finding?':'确定删除该发现项吗？','Severity':'风险等级','Description':'描述','File':'文件','Line':'行','Secret Value':'敏感值','STARTTLS':'STARTTLS','SSL':'SSL','Scan ID':'扫描 ID'
};
const translate = (text:string) => extraZhCN[text] ?? translateText(text);

function translateElement(root: Node, locale: Locale) {
  const elements: Element[] = root instanceof Element ? [root] : [];
  if (root instanceof Element || root instanceof Document || root instanceof DocumentFragment) elements.push(...Array.from(root.querySelectorAll('*')));
  for (const element of elements) for (const attribute of ['placeholder','title','aria-label']) {
    const current=element.getAttribute(attribute); if(current===null) continue; let originals=originalAttributes.get(element); if(!originals){originals=new Map();originalAttributes.set(element,originals);} if(!originals.has(attribute)) originals.set(attribute,current); const source=originals.get(attribute)??current; const next=locale==='zh-CN'?translate(source):source; if(current!==next) element.setAttribute(attribute,next);
  }
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); const nodes:Text[]=root instanceof Text?[root]:[]; while(walker.nextNode()) nodes.push(walker.currentNode as Text);
  for(const node of nodes){const current=node.nodeValue??'';if(!current.trim())continue;if(!originalText.has(node))originalText.set(node,current);let source=originalText.get(node)??current;const previousTrimmed=source.trim();const previousTranslation=source.replace(previousTrimmed,translate(previousTrimmed));if(current!==source&&current!==previousTranslation){originalText.set(node,current);source=current;}const trimmed=source.trim();const translated=locale==='zh-CN'?translate(trimmed):trimmed;const next=source.replace(trimmed,translated);if(current!==next)node.nodeValue=next;}
}

export const LanguageProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [locale,setLocaleState]=useState<Locale>(()=>{const saved=localStorage.getItem('gitalerts-locale');if(saved==='en'||saved==='zh-CN')return saved;return navigator.language.toLowerCase().startsWith('zh')?'zh-CN':'en';});
  const setLocale=(next:Locale)=>{localStorage.setItem('gitalerts-locale',next);setLocaleState(next);};
  useEffect(()=>{document.documentElement.lang=locale;void i18n.changeLanguage(locale);const apply=()=>translateElement(document.body,locale);apply();if(locale==='en')return;const observer=new MutationObserver(mutations=>{observer.disconnect();for(const mutation of mutations){if(mutation.type==='characterData'&&mutation.target.parentNode)translateElement(mutation.target.parentNode,locale);if(mutation.type==='attributes')translateElement(mutation.target,locale);mutation.addedNodes.forEach(node=>translateElement(node,locale));}observer.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['placeholder','title','aria-label']});});observer.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['placeholder','title','aria-label']});return()=>observer.disconnect();},[locale]);
  const value=useMemo(()=>({locale,setLocale,t:(text:string)=>locale==='zh-CN'?extraZhCN[text]??i18n.t(text,{defaultValue:translateText(text)}):text}),[locale]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};
// eslint-disable-next-line react-refresh/only-export-components
export function useLanguage(){const context=useContext(LanguageContext);if(!context)throw new Error('useLanguage must be used within LanguageProvider');return context;}
