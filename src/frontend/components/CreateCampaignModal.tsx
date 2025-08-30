'use client';

import { useState } from 'react';
import { X, Plus, Minus, Calendar, Globe } from 'lucide-react';

interface CampaignFormData {
  client_name: string;
  campaign_name: string;
  client_domain: string;
  campaign_url: string;
  launch_date: string;
  serp_keywords: string[];
  verification_keywords: string[];
  blacklist_domains: string[];
}

interface CreateCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CampaignFormData) => Promise<void>;
  isLoading?: boolean;
}

export function CreateCampaignModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isLoading = false 
}: CreateCampaignModalProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<CampaignFormData>({
    client_name: '',
    campaign_name: '',
    client_domain: '',
    campaign_url: '',
    launch_date: '',
    serp_keywords: [''],
    verification_keywords: [''],
    blacklist_domains: ['']
  });

  const [errors, setErrors] = useState<Partial<CampaignFormData>>({});

  const handleInputChange = (field: keyof CampaignFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleArrayChange = (field: 'serp_keywords' | 'verification_keywords' | 'blacklist_domains', index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const addArrayItem = (field: 'serp_keywords' | 'verification_keywords' | 'blacklist_domains') => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayItem = (field: 'serp_keywords' | 'verification_keywords' | 'blacklist_domains', index: number) => {
    if (formData[field].length > 1) {
      setFormData(prev => ({
        ...prev,
        [field]: prev[field].filter((_, i) => i !== index)
      }));
    }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<CampaignFormData> = {};

    if (step === 1) {
      if (!formData.client_name.trim()) newErrors.client_name = 'Client name is required';
      if (!formData.campaign_name.trim()) newErrors.campaign_name = 'Campaign name is required';
      if (!formData.client_domain.trim()) newErrors.client_domain = 'Client domain is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 3));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    try {
      // Clean up empty array items and ensure non-empty arrays
      const cleanedData = {
        ...formData,
        serp_keywords: formData.serp_keywords.filter(k => k.trim()) || [''],
        verification_keywords: formData.verification_keywords.filter(k => k.trim()) || [''],
        blacklist_domains: formData.blacklist_domains.filter(d => d.trim())
      };

      // Ensure required fields are not empty
      if (!cleanedData.client_name.trim() || !cleanedData.campaign_name.trim() || !cleanedData.client_domain.trim()) {
        console.error('Missing required fields');
        return;
      }

      console.log('Submitting campaign data:', cleanedData);
      await onSubmit(cleanedData);
      
      // Reset form
      setFormData({
        client_name: '',
        campaign_name: '',
        client_domain: '',
        campaign_url: '',
        launch_date: '',
        serp_keywords: [''],
        verification_keywords: [''],
        blacklist_domains: ['']
      });
      setCurrentStep(1);
      setErrors({});
    } catch (error) {
      console.error('Failed to create campaign:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Create New Campaign</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isLoading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step}
                </div>
                <div className="ml-2 text-sm">
                  {step === 1 && 'Basic Info'}
                  {step === 2 && 'Keywords'}
                  {step === 3 && 'Settings'}
                </div>
                {step < 3 && (
                  <div className={`ml-4 h-0.5 w-16 ${
                    step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <div className="p-6">
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Name *
                </label>
                <input
                  type="text"
                  value={formData.client_name}
                  onChange={(e) => handleInputChange('client_name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500 ${
                    errors.client_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., Acme Corporation"
                />
                {errors.client_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.client_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign Name *
                </label>
                <input
                  type="text"
                  value={formData.campaign_name}
                  onChange={(e) => handleInputChange('campaign_name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500 ${
                    errors.campaign_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., Q1 2025 Product Launch"
                />
                {errors.campaign_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.campaign_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Domain *
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    value={formData.client_domain}
                    onChange={(e) => handleInputChange('client_domain', e.target.value)}
                    className={`w-full pl-10 pr-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500 ${
                      errors.client_domain ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="example.com"
                  />
                </div>
                {errors.client_domain && (
                  <p className="mt-1 text-sm text-red-600">{errors.client_domain}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign URL (Optional)
                </label>
                <input
                  type="url"
                  value={formData.campaign_url}
                  onChange={(e) => handleInputChange('campaign_url', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                  placeholder="https://example.com/product-launch"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Launch Date (Optional)
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="date"
                    value={formData.launch_date}
                    onChange={(e) => handleInputChange('launch_date', e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Keywords */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SERP Monitoring Keywords
                </label>
                <p className="text-sm text-gray-500 mb-3">
                  Keywords to monitor in Google search results (checked every 24 hours)
                </p>
                {formData.serp_keywords.map((keyword, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      value={keyword}
                      onChange={(e) => handleArrayChange('serp_keywords', index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                      placeholder="e.g., best project management software"
                    />
                    <button
                      type="button"
                      onClick={() => removeArrayItem('serp_keywords', index)}
                      className="p-2 text-red-600 hover:text-red-800"
                      disabled={formData.serp_keywords.length === 1}
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addArrayItem('serp_keywords')}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add keyword
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Coverage Verification Keywords
                </label>
                <p className="text-sm text-gray-500 mb-3">
                  Keywords to search for in scraped content to verify coverage
                </p>
                {formData.verification_keywords.map((keyword, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      value={keyword}
                      onChange={(e) => handleArrayChange('verification_keywords', index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                      placeholder="e.g., Acme Corporation, product launch"
                    />
                    <button
                      type="button"
                      onClick={() => removeArrayItem('verification_keywords', index)}
                      className="p-2 text-red-600 hover:text-red-800"
                      disabled={formData.verification_keywords.length === 1}
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addArrayItem('verification_keywords')}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add keyword
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Settings */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Domain Blacklist (Optional)
                </label>
                <p className="text-sm text-gray-500 mb-3">
                  Domains to exclude from campaign results
                </p>
                {formData.blacklist_domains.map((domain, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="text"
                      value={domain}
                      onChange={(e) => handleArrayChange('blacklist_domains', index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                      placeholder="e.g., spammy-site.com"
                    />
                    <button
                      type="button"
                      onClick={() => removeArrayItem('blacklist_domains', index)}
                      className="p-2 text-red-600 hover:text-red-800"
                      disabled={formData.blacklist_domains.length === 1}
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addArrayItem('blacklist_domains')}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add domain
                </button>
              </div>

              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Campaign Summary</h4>
                <div className="text-sm text-blue-800 space-y-1">
                  <p><strong>Client:</strong> {formData.client_name}</p>
                  <p><strong>Campaign:</strong> {formData.campaign_name}</p>
                  <p><strong>Domain:</strong> {formData.client_domain}</p>
                  {formData.campaign_url && <p><strong>URL:</strong> {formData.campaign_url}</p>}
                  {formData.launch_date && <p><strong>Launch:</strong> {formData.launch_date}</p>}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t">
          <div>
            {currentStep > 1 && (
              <button
                onClick={handlePrevious}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={isLoading}
              >
                Previous
              </button>
            )}
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={isLoading}
            >
              Cancel
            </button>
            
            {currentStep < 3 ? (
              <button
                onClick={handleNext}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
                disabled={isLoading}
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
                disabled={isLoading}
              >
                {isLoading ? 'Creating...' : 'Create Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
