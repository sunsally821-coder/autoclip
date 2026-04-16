import React, { useEffect, useMemo, useState } from 'react'
import {
  Layout,
  Card,
  Form,
  Input,
  Button,
  Typography,
  Space,
  Alert,
  Divider,
  Row,
  Col,
  Tabs,
  message,
  Select,
  Tag,
} from 'antd'
import {
  KeyOutlined,
  SaveOutlined,
  ApiOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  UserOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { settingsApi } from '../services/api'
import BilibiliManager from '../components/BilibiliManager'
import './SettingsPage.css'

const { Content } = Layout
const { Title, Text, Paragraph } = Typography

type ProviderKey = 'dashscope' | 'openai' | 'gemini' | 'siliconflow'

interface ProviderConfig {
  name: string
  color: string
  description: string
  apiKeyField: string
  placeholder: string
}

interface ModelOption {
  name: string
  display_name: string
  max_tokens?: number
}

const providerConfig: Record<ProviderKey, ProviderConfig> = {
  dashscope: {
    name: 'DashScope',
    color: '#1890ff',
    description: 'Alibaba Tongyi Qianwen',
    apiKeyField: 'dashscope_api_key',
    placeholder: 'Enter your DashScope API key',
  },
  openai: {
    name: 'OpenAI',
    color: '#52c41a',
    description: 'OpenAI GPT models',
    apiKeyField: 'openai_api_key',
    placeholder: 'Enter your OpenAI API key',
  },
  gemini: {
    name: 'Gemini',
    color: '#faad14',
    description: 'Google Gemini models',
    apiKeyField: 'gemini_api_key',
    placeholder: 'Enter your Gemini API key',
  },
  siliconflow: {
    name: 'SiliconFlow',
    color: '#722ed1',
    description: 'SiliconFlow hosted models',
    apiKeyField: 'siliconflow_api_key',
    placeholder: 'Enter your SiliconFlow API key',
  },
}

const SettingsPageRoute: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [showBilibiliManager, setShowBilibiliManager] = useState(false)
  const [availableModels, setAvailableModels] = useState<Record<string, ModelOption[]>>({})
  const [currentProvider, setCurrentProvider] = useState<Record<string, any>>({})
  const [selectedProvider, setSelectedProvider] = useState<ProviderKey>('dashscope')

  const selectedProviderConfig = useMemo(
    () => providerConfig[selectedProvider],
    [selectedProvider],
  )

  useEffect(() => {
    void loadData()
  }, [])

  const loadData = async () => {
    try {
      const [settings, models, provider] = await Promise.all([
        settingsApi.getSettings(),
        settingsApi.getAvailableModels(),
        settingsApi.getCurrentProvider(),
      ])

      const providerValue = (settings?.llm_provider || 'dashscope') as ProviderKey
      setAvailableModels(models || {})
      setCurrentProvider(provider || {})
      setSelectedProvider(providerValue)
      form.setFieldsValue(settings || {})
    } catch (error) {
      console.error('Failed to load settings data:', error)
      message.error('Failed to load settings')
    }
  }

  const handleSave = async (values: Record<string, any>) => {
    try {
      setLoading(true)
      await settingsApi.updateSettings(values)
      message.success('Settings saved')
      await loadData()
    } catch (error: any) {
      message.error(`Save failed: ${error?.message || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleTestApiKey = async () => {
    const apiKey = form.getFieldValue(selectedProviderConfig.apiKeyField)
    const modelName = form.getFieldValue('model_name')

    if (!apiKey) {
      message.error('Enter an API key first')
      return
    }

    if (!modelName) {
      message.error('Choose a model first')
      return
    }

    try {
      setLoading(true)
      const result = await settingsApi.testApiKey(selectedProvider, apiKey, modelName)
      if (result.success) {
        message.success('API key test succeeded')
      } else {
        message.error(`API key test failed: ${result.error || 'Unknown error'}`)
      }
    } catch (error: any) {
      message.error(`API key test failed: ${error?.message || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleProviderChange = (provider: ProviderKey) => {
    setSelectedProvider(provider)
    form.setFieldsValue({ llm_provider: provider, model_name: undefined })
  }

  const aiSettingsContent = (
    <>
      <Card title="AI Provider Settings" className="settings-card">
        <Alert
          message="Multiple providers supported"
          description="Configure the provider, API key, and model your pipeline should use."
          type="info"
          showIcon
          className="settings-alert"
        />

        <Form
          form={form}
          layout="vertical"
          className="settings-form"
          onFinish={(values) => void handleSave(values)}
          initialValues={{
            llm_provider: 'dashscope',
            model_name: 'qwen-plus',
            chunk_size: 5000,
            min_score_threshold: 0.7,
            max_clips_per_collection: 5,
          }}
        >
          {currentProvider.available && (
            <Alert
              message={`Current provider: ${currentProvider.display_name || selectedProvider} - ${currentProvider.model || ''}`}
              type="success"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          <Form.Item
            label="Provider"
            name="llm_provider"
            className="form-item"
            rules={[{ required: true, message: 'Choose a provider' }]}
          >
            <Select
              value={selectedProvider}
              onChange={handleProviderChange}
              className="settings-input"
              placeholder="Choose a provider"
            >
              {Object.entries(providerConfig).map(([key, config]) => (
                <Select.Option key={key} value={key}>
                  <Space>
                    <span style={{ color: config.color }}>
                      <RobotOutlined />
                    </span>
                    <span>{config.name}</span>
                    <Tag color={config.color}>{config.description}</Tag>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label={`${selectedProviderConfig.name} API Key`}
            name={selectedProviderConfig.apiKeyField}
            className="form-item"
            rules={[
              { required: true, message: 'Enter an API key' },
              { min: 10, message: 'API key looks too short' },
            ]}
          >
            <Input.Password
              placeholder={selectedProviderConfig.placeholder}
              prefix={<KeyOutlined />}
              className="settings-input"
            />
          </Form.Item>

          <Form.Item
            label="Model"
            name="model_name"
            className="form-item"
            rules={[{ required: true, message: 'Choose a model' }]}
          >
            <Select
              className="settings-input"
              placeholder="Choose a model"
              showSearch
              optionFilterProp="label"
            >
              {(availableModels[selectedProvider] || []).map((model) => (
                <Select.Option
                  key={model.name}
                  value={model.name}
                  label={model.display_name}
                >
                  <Space>
                    <span>{model.display_name}</span>
                    {model.max_tokens !== undefined && (
                      <Tag>{model.max_tokens} tokens</Tag>
                    )}
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item className="form-item">
            <Space>
              <Button
                type="default"
                icon={<ApiOutlined />}
                className="test-button"
                onClick={() => void handleTestApiKey()}
                loading={loading}
              >
                Test Connection
              </Button>
            </Space>
          </Form.Item>

          <Divider className="settings-divider" />

          <Title level={4} className="section-title">
            Pipeline Settings
          </Title>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Chunk Size" name="chunk_size" className="form-item">
                <Input type="number" placeholder="5000" className="settings-input" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Min Score Threshold" name="min_score_threshold" className="form-item">
                <Input type="number" step="0.1" min="0" max="1" placeholder="0.7" className="settings-input" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Max Clips per Collection" name="max_clips_per_collection" className="form-item">
                <Input type="number" placeholder="5" className="settings-input" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item className="form-item">
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              size="large"
              className="save-button"
              loading={loading}
            >
              Save Settings
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Usage Notes" className="settings-card">
        <Space direction="vertical" size="large" className="instructions-space">
          <div className="instruction-item">
            <Title level={5} className="instruction-title">
              <InfoCircleOutlined /> 1. Choose a provider
            </Title>
            <Paragraph className="instruction-text">
              Pick the model platform you want to use, then enter the matching API key.
            </Paragraph>
          </div>

          <div className="instruction-item">
            <Title level={5} className="instruction-title">
              <InfoCircleOutlined /> 2. Tune the pipeline
            </Title>
            <Paragraph className="instruction-text">
              Chunk size, score threshold, and collection size affect the final clip selection.
            </Paragraph>
          </div>

          <div className="instruction-item">
            <Title level={5} className="instruction-title">
              <InfoCircleOutlined /> 3. Verify before saving
            </Title>
            <Paragraph className="instruction-text">
              Run a connection test after changing providers or keys so failures surface early.
            </Paragraph>
          </div>
        </Space>
      </Card>
    </>
  )

  const bilibiliContent = (
    <Card title="Bilibili Account Tools" className="settings-card">
      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
        <div style={{ marginBottom: 24 }}>
          <UserOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={3} style={{ color: '#ffffff', margin: '0 0 8px 0' }}>
            Manage Bilibili Accounts
          </Title>
          <Text type="secondary" style={{ color: '#b0b0b0', fontSize: 16 }}>
            Maintain uploader accounts and upload preferences in one place.
          </Text>
        </div>

        <Space size="large">
          <Button
            type="primary"
            size="large"
            icon={<UserOutlined />}
            onClick={() => setShowBilibiliManager(true)}
            style={{
              borderRadius: 8,
              background: 'linear-gradient(45deg, #1890ff, #36cfc9)',
              border: 'none',
              fontWeight: 500,
              height: 48,
              padding: '0 32px',
              fontSize: 16,
            }}
          >
            Open Manager
          </Button>
        </Space>

        <div style={{ marginTop: 32, textAlign: 'left', maxWidth: 600, marginInline: 'auto' }}>
          <Title level={4} style={{ color: '#ffffff', marginBottom: 16 }}>
            Highlights
          </Title>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
            <Card size="small">Store multiple uploader accounts</Card>
            <Card size="small">Reuse cookies instead of logging in repeatedly</Card>
            <Card size="small">Prepare uploads directly from clip pages</Card>
            <Card size="small">Track upload records in one view</Card>
          </div>
        </div>
      </div>
    </Card>
  )

  return (
    <Content className="settings-page">
      <div className="settings-container">
        <Title level={2} className="settings-title">
          <SettingOutlined /> Settings
        </Title>

        <Tabs
          defaultActiveKey="api"
          className="settings-tabs"
          items={[
            { key: 'api', label: 'AI Settings', children: aiSettingsContent },
            { key: 'bilibili', label: 'Bilibili', children: bilibiliContent },
          ]}
        />

        <BilibiliManager
          visible={showBilibiliManager}
          onClose={() => setShowBilibiliManager(false)}
          onUploadSuccess={() => {
            message.success('Operation completed')
          }}
        />
      </div>
    </Content>
  )
}

export default SettingsPageRoute
