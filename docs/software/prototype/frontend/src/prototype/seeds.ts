import type {
  DemoUser,
  Evidence,
  PrototypeQuestion,
  QuestionVersion,
} from './types'

export const demoUsers: DemoUser[] = [
  {
    id: 1,
    username: 'teacher',
    password: 'Teacher123',
    email: 'teacher@example.com',
    role: 'TEACHER',
    is_active: true,
    created_at: '2026-10-01T08:00:00+08:00',
    updated_at: '2026-10-01T08:00:00+08:00',
  },
  {
    id: 2,
    username: 'admin',
    password: 'Admin123',
    email: 'admin@example.com',
    role: 'ADMIN',
    is_active: true,
    created_at: '2026-10-01T08:00:00+08:00',
    updated_at: '2026-10-01T08:00:00+08:00',
  },
  {
    id: 3,
    username: 'physics_li',
    password: 'Teacher123',
    email: 'li@example.com',
    role: 'TEACHER',
    is_active: true,
    created_at: '2026-10-05T08:00:00+08:00',
    updated_at: '2026-10-05T08:00:00+08:00',
  },
]

const samples = [
  {
    topic: '牛顿第二定律',
    title: '水平面上物块的加速运动',
    content:
      '质量为 $m=2\\,\\mathrm{kg}$ 的物块放在光滑水平面上，受到水平向右的恒力 $F=6\\,\\mathrm{N}$。物块由静止开始运动，求加速度大小及 $2\\,\\mathrm{s}$ 末的速度。',
    answer: '$a=3\\,\\mathrm{m/s^2}$，$v=6\\,\\mathrm{m/s}$。',
    explanation:
      '物块竖直方向受力平衡，水平方向合力为 $F$。根据牛顿第二定律，$a=F/m=3\\,\\mathrm{m/s^2}$；由 $v=at$ 得 $v=6\\,\\mathrm{m/s}$。',
    choices: {
      A: '$3\\,\\mathrm{m/s^2}$；$6\\,\\mathrm{m/s}$',
      B: '$6\\,\\mathrm{m/s^2}$；$12\\,\\mathrm{m/s}$',
      C: '$2\\,\\mathrm{m/s^2}$；$4\\,\\mathrm{m/s}$',
      D: '$1.5\\,\\mathrm{m/s^2}$；$3\\,\\mathrm{m/s}$',
    },
    image: '/illustrations/newton.svg',
    source: '普通高中物理课程标准（2017年版2020年修订）·运动和力',
    evidence: '运用牛顿运动定律解释生产生活中的有关现象，解决有关问题。',
  },
  {
    topic: '欧姆定律',
    title: '串联电路中的电流与电压',
    content:
      '理想电源电压为 $U=12\\,\\mathrm{V}$，电阻 $R_1=4\\,\\Omega$、$R_2=8\\,\\Omega$ 串联接入电路，导线电阻不计。求电路中的电流和 $R_2$ 两端的电压。',
    answer: '$I=1\\,\\mathrm{A}$，$U_2=8\\,\\mathrm{V}$。',
    explanation:
      '串联总电阻 $R=R_1+R_2=12\\,\\Omega$。由欧姆定律 $I=U/R=1\\,\\mathrm{A}$，所以 $U_2=IR_2=8\\,\\mathrm{V}$。',
    choices: {
      A: '$1\\,\\mathrm{A}$；$8\\,\\mathrm{V}$',
      B: '$2\\,\\mathrm{A}$；$16\\,\\mathrm{V}$',
      C: '$1.5\\,\\mathrm{A}$；$12\\,\\mathrm{V}$',
      D: '$3\\,\\mathrm{A}$；$24\\,\\mathrm{V}$',
    },
    image: '/illustrations/circuit.svg',
    source: '普通高中物理课程标准·电路及其应用',
    evidence: '理解欧姆定律，能分析简单串联与并联电路。',
  },
  {
    topic: '机械能守恒',
    title: '自由下落过程中的能量转化',
    content:
      '质量为 $m=1\\,\\mathrm{kg}$ 的小球从离地 $h=5\\,\\mathrm{m}$ 处由静止释放。忽略空气阻力，取 $g=10\\,\\mathrm{m/s^2}$，求小球落地前瞬间的速度大小。',
    answer: '$v=10\\,\\mathrm{m/s}$。',
    explanation:
      '以地面为重力势能零点，重力势能转化为动能：$mgh=\\frac{1}{2}mv^2$，所以 $v=\\sqrt{2gh}=10\\,\\mathrm{m/s}$。',
    choices: {
      A: '$10\\,\\mathrm{m/s}$',
      B: '$5\\,\\mathrm{m/s}$',
      C: '$50\\,\\mathrm{m/s}$',
      D: '$100\\,\\mathrm{m/s}$',
    },
    image: '/illustrations/fall.svg',
    source: '普通高中物理课程标准·机械能及其守恒定律',
    evidence: '理解机械能守恒定律及其适用条件，能解决简单的能量转化问题。',
  },
]

export function snapshot(
  q: PrototypeQuestion,
  source: 'system' | 'teacher',
): QuestionVersion {
  return {
    version: q.version,
    title: q.title,
    content: q.content,
    options: q.options,
    answer: q.answer,
    explanation: q.explanation,
    illustration_url: q.illustration_url,
    created_at: q.updated_at,
    source,
  }
}

export function makeExample(
  topic: string,
  index = 0,
  type = 'short_answer',
): Omit<PrototypeQuestion, 'id' | 'user_id' | 'task_id'> {
  const sample =
    samples.find(
      (s) =>
        topic.includes(s.topic) ||
        (s.topic === '欧姆定律' && /电路|电阻|电学/.test(topic)) ||
        (s.topic === '牛顿第二定律' && /力|加速/.test(topic)) ||
        (s.topic === '机械能守恒' && /能|自由落体/.test(topic)),
    ) || samples[index % samples.length]
  const now = new Date().toISOString()
  const evidence: Evidence[] = [
    {
      source: sample.source,
      fragment_id: `DEMO-${samples.indexOf(sample) + 1}-001`,
      index_version: 'demo-index-v1',
      content: sample.evidence,
    },
  ]
  let content = sample.content
  let answer = sample.answer
  let options: string | undefined
  if (type === 'single_choice' || type === 'multiple_choice') {
    options = JSON.stringify(sample.choices)
    answer = 'A'
    content +=
      type === 'multiple_choice'
        ? '\n请选择全部正确选项（本题仅有一个正确选项）。'
        : '\n请选择正确选项。'
    if (type === 'multiple_choice') {
      options = JSON.stringify({
        ...sample.choices,
        D: `解析所依据的物理规律是${sample.topic === '欧姆定律' ? '欧姆定律' : sample.topic === '机械能守恒' ? '机械能守恒定律' : '牛顿第二定律'}。`,
      })
      answer = 'A、D'
      content = content.replace('（本题仅有一个正确选项）', '')
    }
  } else if (type === 'fill_blank') content += '\n请将计算结果填入：________。'
  return {
    title: sample.title,
    content,
    question_type: type,
    grade: sample.topic === '欧姆定律' ? '高二' : '高一',
    bloom_level: 'apply',
    difficulty: '中等',
    knowledge_point: sample.topic,
    options,
    answer,
    explanation: sample.explanation,
    illustration_url: sample.image,
    require_illustration: true,
    created_at: now,
    updated_at: now,
    rating: 0,
    comment: '',
    teacher_status: 'pending',
    version: 1,
    versions: [],
    evidence,
    kb_reason: '使用预置来源片段演示引用链路；未执行实际向量检索。',
    confirmations: [],
  }
}

export function seedQuestions(): PrototypeQuestion[] {
  return Array.from({ length: 14 }, (_, i) => {
    const q: PrototypeQuestion = {
      ...makeExample(
        samples[i % 3].topic,
        i,
        ['single_choice', 'multiple_choice', 'fill_blank', 'short_answer'][
          i % 4
        ],
      ),
      id: i + 1,
      user_id: i < 12 ? 1 : 3,
      task_id: 'DEMO-INITIAL',
    }
    q.created_at = q.updated_at = new Date(
      Date.now() - (i + 1) * 3600000 * 8,
    ).toISOString()
    q.bloom_level = ['remember', 'understand', 'apply', 'analyze'][i % 4]
    q.difficulty = ['基础', '中等', '困难'][i % 3]
    q.thinking_tags = [
      ['C1', 'C2'],
      ['C2', 'C6'],
      ['C2', 'C3'],
    ][i % 3]
    q.rating = i % 3 === 0 ? 5 : i % 3 === 1 ? 4 : 0
    if (i % 3 !== 2) {
      q.teacher_status = 'confirmed'
      q.confirmations = [
        {
          version: 1,
          teacher_id: q.user_id,
          teacher_name: q.user_id === 1 ? 'teacher' : 'physics_li',
          confirmed_at: q.updated_at,
        },
      ]
    }
    q.versions = [snapshot(q, 'system')]
    return q
  })
}
