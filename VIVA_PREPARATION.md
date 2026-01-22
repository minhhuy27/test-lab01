# 📚 CHUẨN BỊ VẤNĐÁP - Lab 01 Blockchain

## 🎯 MỤC TIÊU
Tài liệu này tổng hợp **kiến thức cần nhớ** và **câu trả lời tiêu chuẩn** cho kỳ vấn đáp Lab 01 Blockchain.

---

## 📖 PHẦN 1: HIỂU VỀ KIẾN THỨC NỀN TẢNG

### 1.1 Lab Là Gì?
**Câu hỏi**: *"Lab 01 là gì? Mục tiêu chính là gì?"*

**Trả lời**:
> Lab 01 là bài tập xây dựng một **Layer 1 blockchain tối giản** với các đặc tính:
> - **Mạng không tin cậy**: Gói tin có thể bị trễ (delay), mất (drop), hoặc nhân đôi (duplicate)
> - **Đồng thuận 2 pha**: Sử dụng Prevote → Precommit để finalize block
> - **Thực thi xác định**: Tất cả node sẽ tính cùng một state hash khi apply cùng một chuỗi transaction
> - **Liveness**: Khi network bình thường, mới block sẽ được finalize
>
> **Mục tiêu**: Tất cả node chính (honest) phải hội tụ (converge) đến cùng một chuỗi block được finalize, bất kể network gặp phải delay, drop hay duplicate.

---

### 1.2 Kiến Thức Cơ Bản Cần Nhớ

#### A. **State, Transaction, Block, Vote** (4 khái niệm chính)

| Khái Niệm | Định Nghĩa | Ví Dụ |
|-----------|-----------|--------|
| **State** | Data mà network đồng ý (key-value store) | `{"Alice/balance": 100, "Bob/balance": 50}` |
| **Transaction** | Request ký được thay đổi state | Alice gửi: `{"key": "Alice/balance", "value": 99, "signature": "..."}` |
| **Block** | Tập hợp transaction đã được sắp xếp + parent hash | Height 1: 10 tx, parent="genesis", state_root="..." |
| **Vote** | Tuyên bố ký của validator ủng hộ block | "Tôi (validator 0) prevote cho block_hash_XYZ ở height 1" |

#### B. **Thuật Toán Đồng Thuận**

```
Vòng Consensus:
1. Proposer gửi proposal (block) → tất cả node
2. Node nhận block → broadcast PREVOTE cho block đó
3. Khi node thấy ≥ 2/3+1 PREVOTE → broadcast PRECOMMIT
4. Khi node thấy ≥ 2/3+1 PRECOMMIT → FINALIZE block
5. Block được finalize → add vào ledger

Threshold = ⌊2/3 * n⌋ + 1
Ví dụ: 4 node → threshold = (4*2)/3 + 1 = 3 votes
```

#### C. **Mã Hóa & Ký**

- **Ed25519**: Scheme ký (dùng public/private key)
- **SHA-256**: Hash (dùng tính state_root, block_hash)
- **Domain Separation**: Prefix vào message trước ký:
  - TX message: `TX:chain_id|{...payload...}`
  - HEADER message: `HEADER:chain_id|{...payload...}`
  - VOTE message: `VOTE:chain_id|{...payload...}`
  
  **Lý do**: Ngăn chặn signature reuse (một signature cho TX không được dùng cho HEADER)

#### D. **Determinism**

- **Ý tưởng**: Chạy 2 lần cùng input → kết quả phải giống bit-by-bit
- **Cách đạt**: 
  - RNG seeded cố định
  - JSON canonical (sorted keys, no spaces)
  - Ordered transaction execution
- **Kiểm tra**: Run 2x, so sánh logs và state_hash phải bằng nhau

---

## 📋 PHẦN 2: CẤU TRÚC MÃ - KIẾN THỨC THIẾT YẾU

### 2.1 Cấu Trúc Thư Mục

```
src/
├── crypto/           # Ký (Ed25519), xác minh signature
│   ├── keys.py       # Generate keypair, load public/private key
│   └── signing.py    # sign_message(), verify_signature()
│
├── encoding/         # Mã hóa xác định
│   └── codec.py      # canonical_json(), encode_tx_for_signing(), ...
│
├── execution/        # Thực thi transaction & block
│   └── execution.py  # ExecutionState, Transaction, Block
│
├── network/          # Mô phỏng mạng không tin cậy
│   └── simulator.py  # NetworkSimulator (delay, drop, dup, backpressure)
│
├── consensus/        # Logic đồng thuận
│   ├── engine.py     # ConsensusEngine (đếm vote, check threshold)
│   ├── messages.py   # Vote class
│   └── controller.py # Controller tùy chọn
│
└── simulator/        # Demo node, block, ledger
    ├── block.py      # BlockHeader, Block
    ├── ledger.py     # Ledger (lưu block)
    ├── node.py       # Node mô phỏng
    └── harness.py    # run_consensus_smoke_simple() helper
```

### 2.2 Các Lớp (Class) Quan Trọng

#### **ExecutionState** [execution/execution.py]
```python
class ExecutionState:
    - state: Dict[str, Any]           # Key-value store
    - ledger: List[Dict]              # Các block đã finalize
    - apply_transaction(tx, verify_fn) # Thêm tx vào state
    - apply_block(block, verify_fn)    # Thêm block vào ledger
    - compute_state_root()             # Merkle hash của state
```

**Ứng dụng**: 
- Lưu state, apply transaction một cách xác định
- Compute state_root (Merkle tree)

#### **Transaction** [execution/execution.py]
```python
@dataclass
class Transaction:
    sender: str              # Người gửi
    key: str                 # Khóa muốn sửa
    value: Any               # Giá trị mới
    signature: bytes         # Chữ ký (raw bytes)
    pubkey: bytes            # Khóa công khai
    
    def to_signing_bytes(chain_id: str) -> bytes:
        # Trả về bytes để verify signature
        # Format: "TX:chain_id|{...sorted...}"
```

#### **NetworkSimulator** [network/simulator.py]
```python
class NetworkSimulator:
    - register_node(node_id, handler)        # Đăng ký node
    - send_header(sender, receiver, ...)     # Gửi header
    - send_body(sender, receiver, ...)       # Gửi body (sau header)
    - run_until_idle()                       # Chạy mô phỏng
    - logs()                                 # Lấy log events
    
    # Tham số cấu hình:
    - base_delay_ms: int          # Delay tối thiểu
    - jitter_ms: int              # Delay ngẫu nhiên thêm
    - drop_rate: float            # Xác suất drop [0,1]
    - duplicate_rate: float       # Xác suất nhân đôi [0,1]
    - link_bandwidth_bytes_per_ms # Băng thông giả lập
```

**Ứng dụng**:
- Mô phỏng mạng không tin cậy (delay, drop, dup)
- Giới hạn throughput (backpressure)
- Header → Body ordering (header phải tới trước body)

#### **ConsensusEngine** [consensus/engine.py]
```python
class ConsensusEngine:
    - votes: defaultdict          # votes[height][phase][block_hash] = set(validators)
    - process_vote(vote)          # Thêm vote, check threshold
    - total_nodes: int            # Số node
    
    # Logic:
    threshold = (total_nodes * 2) // 3 + 1
    Khi count(votes) >= threshold:
        Nếu phase == "PREVOTE" → return "SEND_PRECOMMIT"
        Nếu phase == "PRECOMMIT" → return "FINALIZE_BLOCK"
```

#### **Block, BlockHeader** [simulator/block.py]
```python
@dataclass
class BlockHeader:
    height: int              # Height của block
    parent_hash: str         # Hash của block cha
    state_hash: str          # State commitment
    proposer: str            # Người propose
    signature: str           # Ký của proposer (nếu có)

@dataclass
class Block:
    header: BlockHeader
    transactions: List[Dict]
    
    @property
    def hash(self) -> str:
        return compute_block_hash(self.header)
```

#### **Ledger** [simulator/ledger.py]
```python
class Ledger:
    - _blocks: List[Block]           # Blocks được finalize
    - append_finalized_block(block)  # Add block (check parent)
    - last_hash()                    # Hash của block cuối
    - height()                       # Số block (height)
```

---

## 💡 PHẦN 3: CÁC CÂUHỎI CÓ THỂĐƯỢC HỎI & TRẢ LỜI

### 3.1 **Câu Hỏi Về Mạng (Network)**

#### Q1: "Tại sao cần phân biệt send_header() và send_body()?"
**Trả lời**:
> Yêu cầu: "Headers are broadcast before bodies; a body may be sent only after the receiver accepts the matching header."
>
> Mục đích: Ngăn chặn tình huống body tới trước header:
> - Nếu body tới trước → receiver không biết có header nào → drop body
> - Sau đó header tới → receiver nhận nhưng body đã mất
>
> **Triển khai**:
> - send_header(sender, receiver, header_id, height, payload): Ghi log `_seen_headers[header_id] = True`
> - send_body(sender, receiver, body_id, header_id): Check `if header_id in _seen_headers` → deliver; else reject

#### Q2: "Backpressure là gì? Tại sao cần?"
**Trả lời**:
> **Backpressure** = Giới hạn số gói đang "bay" (inflight) trên link.
>
> **Lý do**:
> - Nếu proposer gửi quá nhanh → network buffer full → gói bị drop
> - Ngăn node được spam nhận gói
>
> **Cách làm**:
> - Track `_inflight_count[sender]` ≤ max_inflight_per_sender
> - Track `_inflight_bytes_link[(s,r)]` ≤ max_bytes_inflight_per_link
> - Nếu vượt → drop message hoặc queue chờ
> - Nếu quá cao → auto_block link tạm thời

#### Q3: "Làm thế nào drop/duplicate được xử lý?"
**Trả lời**:
> ```python
> # Trong NetworkSimulator.send_message():
> if random() < drop_rate:
>     _log_event("drop", ...)
>     return  # Gói bị drop
>
> if random() < duplicate_rate:
>     # Gửi lại gói lần 2 với msg_id khác
>     queue message thêm một lần
> 
> delay = base_delay + random_jitter
> deliver_at = now + delay
> # Dùng priority queue → deliver theo thứ tự delay
> ```
> 
> **Xử lý bên node**:
> - Duplicate vote: `votes[height][phase][block] = set(validators)` → tự động khử trùng
> - Duplicate tx: Phụ thuộc app logic (trong lab không xử lý explicit nonce)

#### Q4: "Tôpô là gì? Làm sao load từ file?"
**Trả lời**:
> **Tôpô** = Danh sách directed edges (sender, receiver) → quyết định node nào có thể gửi tới node nào.
>
> **Mặc định** (nếu không load): Full-mesh (mỗi node gửi được tới tất cả node khác)
>
> **Load từ file**:
> ```python
> def load_topology_from_file(self, path):
>     edges = []
>     with open(path) as f:
>         for line in f:
>             sender, receiver = line.strip().split(',')
>             edges.append((sender, receiver))
>     self._allowed_edges = set(edges)
> ```
> 
> **File format** (CSV):
> ```
> 0,1
> 0,2
> 1,0
> 1,2
> ...
> ```
> (Mỗi dòng: `sender,receiver`)

---

### 3.2 **Câu Hỏi Về Consensus**

#### Q1: "Threshold 2/3+1 là từ đâu? Tại sao?"
**Trả lời**:
> **Công thức**: threshold = ⌊(total_nodes * 2) / 3⌋ + 1
>
> **Ví dụ**:
> - 4 node: (4*2)/3 + 1 = 3 vote
> - 7 node: (7*2)/3 + 1 = 5 vote
> - 10 node: (10*2)/3 + 1 = 7 vote
>
> **Tại sao 2/3+1?**
> - Strict majority: Không thể có 2 nhóm khác nhau mỗi nhóm ≥ threshold
> - BFT assumption: Có thể chịu đc ⌊1/3 * n⌋ Byzantine node
> - Ví dụ 4 node với 1 Byzantine (< 1/3): Cần 3 honest → 3 ≥ 2/3+1 ✓

#### Q2: "Tại sao cần Prevote trước Precommit? Tại sao không gửi thẳng Precommit?"
**Trả lời**:
> **Prevote → Precommit** = Two-phase protocol (Tendermint-style)
>
> **Flow**:
> 1. Prevote: "Tôi thấy block này valid"
> 2. Precommit: "Tôi thấy ≥2/3+1 node cũng thấy block này valid → finalize"
>
> **Lợi ích**:
> - **Safety**: Nếu block A được finalize ở height h → mỗi honest node phải thấy ≥2/3+1 precommit cho A
>   - Khi height h+1 → không thể finalize block B khác ở height h (vì cần ≥2/3+1 precommit, nhưng mỗi node chỉ prevote 1 lần)
>   - Chứng minh: Nếu ≥2/3+1 precommit cho A ở h, thì ít nhất 1/3+1 node là honest → sẽ reject B ở h
>
> - **Liveness**: Cơ hội 2 lần để đồng ý (prevote, precommit) thay vì 1

#### Q3: "Nếu proposer gửi 2 block khác nhau cùng height thì sao?"
**Trả lời**:
> **Scenario**: Proposer gửi block A và block B đều ở height 1
>
> **Kết quả**: Node sẽ:
> 1. Chốt block đầu tiên mà nhận được (FirstSeenNode logic trong test)
> 2. Bỏ qua block khác
> 3. Prevote cho block đầu tiên
>
> **Safety**: Vì node chỉ prevote 1 lần/height → ≥2/3+1 node sẽ prevote cùng 1 block
> → Chỉ 1 block được precommit → Safety guaranteed ✓

#### Q4: "Làm sao xác minh vote?"
**Trả lời**:
> **Vote signature**:
> ```python
> vote = {
>     "height": 1,
>     "block_hash": "abc...",
>     "phase": "PREVOTE",
>     "voter": "node_0"
> }
> 
> msg = encode_vote_for_signing(vote, chain_id="test-chain")
> # msg = "VOTE:test-chain|{...canonical json...}"
> 
> sig = sign_message(privkey, msg)
> verify_signature(pubkey, msg, sig)  # True/False
> ```
>
> **Domain separation**: `VOTE:chain_id` prefix → signature không reuse cho message khác
>
> **Hiện tại (lab)**: `_mock_verify_signature()` trả về True (chưa implement thực)

---

### 3.3 **Câu Hỏi Về Cryptography**

#### Q1: "Domain separation là gì? Tại sao quan trọng?"
**Trả lời**:
> **Domain Separation** = Thêm prefix riêng cho mỗi loại message trước khi ký
>
> **Ví dụ**:
> - TX message: `TX:chain_id|sender=Alice&key=balance&value=99`
> - HEADER message: `HEADER:chain_id|height=1&parent_hash=...&state_hash=...`
> - VOTE message: `VOTE:chain_id|height=1&block_hash=...&phase=PREVOTE`
>
> **Tại sao quan trọng?**
> - **Không domain sep**: Attacker có signature cho TX, có thể dùng lại cho HEADER
> - **Có domain sep**: Signature không xác minh cho loại message khác (khác prefix)
>
> **Code**:
> ```python
> def encode_tx_for_signing(tx, chain_id):
>     return b"TX:" + chain_id.encode() + b"|" + canonical_json(payload)
> ```

#### Q2: "Canonical JSON là gì? Ví dụ?"
**Trả lời**:
> **Canonical JSON** = JSON chuẩn (không ambiguity) cho mỗi object
>
> **Đặc điểm**:
> - Sorted keys: `{"a": 1, "b": 2}` vs `{"b": 2, "a": 1}` → same bytes
> - No spaces: `{"a":1}` (không `{"a": 1}`)
> - UTF-8: ASCII compatible
>
> **Code**:
> ```python
> def canonical_json(data):
>     return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
> ```
>
> **Ví dụ**:
> ```
> d1 = {"sender": "Alice", "key": "A/msg", "value": 1}
> d2 = {"value": 1, "key": "A/msg", "sender": "Alice"}  # Khác thứ tự
> 
> canonical_json(d1) == canonical_json(d2)  # True!
> # Cả 2 → '{"key":"A/msg","sender":"Alice","value":1}'
> ```

#### Q3: "Merkle tree state_root là gì?"
**Trả lời**:
> **State Root** = Single hash đại diện cho toàn bộ state
>
> **Cách tính**:
> ```
> State = {
>     "Alice/balance": 100,
>     "Bob/balance": 50
> }
> 
> Sorted items = [("Alice/balance", 100), ("Bob/balance", 50)]
> 
> Leaves:
>   leaf_1 = hash(["Alice/balance", 100])
>   leaf_2 = hash(["Bob/balance", 50])
> 
> Internal:
>   node = hash(leaf_1 || leaf_2)  # leaf_1 + leaf_2 (concatenate)
> 
> Root = node
> ```
>
> **Tại sao Merkle?**
> - Deterministic: Same state → same root
> - Commit: 1 hash đại diện cho toàn state
> - Efficient: Có thể prove inclusion (trong app thực)

#### Q4: "Tại sao dùng Ed25519 chứ không dùng RSA?"
**Trả lời**:
> **Ed25519**:
> - Nhanh, nhỏ (32-byte keys)
> - Deterministic signature (same message → same signature)
> - Modern, được recommend
>
> **RSA**:
> - Chậm hơn
> - Keysize lớn (2048-4096 bit)
> - Randomized signature (khó replicate)
>
> **Lab chọn Ed25519** vì cần determinism (dễ test)

---

### 3.4 **Câu Hỏi Về Execution & Determinism**

#### Q1: "Determinism là gì? Tại sao quan trọng?"
**Trả lời**:
> **Determinism** = Chạy 2 lần cùng input → output giống bit-by-bit
>
> **Tại sao quan trọng blockchain?**
> - Mỗi node execute block độc lập
> - Nếu không deterministic → node A tính state_root khác node B
> - State khác → fork chain (nguy hiểm)
>
> **Cách đạt trong lab**:
> 1. **RNG seeded**: `random.Random(seed=12345)` → same random sequence
> 2. **Canonical encoding**: JSON sorted keys, no spaces
> 3. **Ordered execution**: Transaction áp dụng theo thứ tự trong block
> 4. **No floating point**: Dùng int/str, không dùng float (float không deterministic)

#### Q2: "Làm sao test determinism?"
**Trả lời**:
> **Method**:
> ```python
> # Run 1
> log1, state_hash1 = run_scenario(seed=12345)
> 
> # Run 2
> log2, state_hash2 = run_scenario(seed=12345)
> 
> # Compare
> assert log1 == log2, "Logs khác nhau"
> assert state_hash1 == state_hash2, "State hash khác"
> ```
>
> **Test files** trong lab:
> - `determinism_check.py`: So sánh log + state_hash tx/state
> - `determinism_consensus_network.py`: So sánh consensus + network log
> - `run_determinism_suite.py`: Chạy cả 2, diff log files

#### Q3: "Nếu transaction execute khác thứ tự thì sao?"
**Trả lời**:
> **Scenario**:
> ```
> Block = [tx_A: Alice balance-=1, tx_B: Bob balance+=1]
> 
> Node 1: A,B → {Alice: 99, Bob: 101}
> Node 2: B,A → {Alice: 99, Bob: 101}  (kết quả same)
> ```
> 
> **Nhưng** nếu có constraint (ví dụ: transfer chỉ được nếu balance > 0):
> ```
> Block = [tx_A: Alice -100 (Alice=0), tx_B: Bob -1 (Bob fails)]
> 
> Order A,B: Alice=0, Bob=50 (B fails)
> Order B,A: Alice=0, Bob=50 (B fails) → same OK
> 
> Nhưng nếu:
> Block = [tx_A: Alice +50, tx_B: Alice -30]
> 
> Order A,B: Alice += 50, -30 → 20
> Order B,A: Alice -= 30 (fails?), +50 → depends
> ```
> 
> **Lab**: Giả sử mỗi tx độc lập, không có constraint → thứ tự không gây vấn đề
> **Thực tế**: Phải có canonical order (block header decide thứ tự)

#### Q4: "State Root được lưu ở đâu?"
**Trả lời**:
> **Trong block header**:
> ```python
> @dataclass
> class BlockHeader:
>     height: int          # Height
>     parent_hash: str     # Hash của cha
>     state_hash: str      # ← State root (commitment)
>     proposer: str        # Proposer
> ```
>
> **Tính toán**:
> ```python
> def apply_block(self, block):
>     for tx in block.txs:
>         self.apply_transaction(tx, ...)
>     state_root = self.compute_state_root()  # Merkle tree
>     # state_root đây có thể add vào block header
> ```
>
> **Dùng để**:
> - Verify block: Kiểm tra state_root match với tính toán lại
> - Commit: Block hash include state_root → commit cả state

---

### 3.5 **Câu Hỏi Về Test**

#### Q1: "Bao nhiêu test? Test cái gì?"
**Trả lời**:
> **Unit Tests (9 tests)**:
> - test_crypto_basic.py: Sign/verify, domain separation
> - test_encoding_basic.py: Canonical JSON, chain_id affects
> - test_block_basic.py: Header signature, hash determinism
> - test_ledger_basic.py: Append block, parent check
> - test_state_basic.py: Apply tx/block, state root
> - test_network_basic.py: Send/receive
> - test_network_drop_duplicate.py: Drop, duplicate
> - test_network_backpressure.py: Rate limiting
> - test_network_integration.py: Header → body
>
> **E2E Tests (5+ tests)**:
> - determinism_check.py: Run 2x, compare log + state
> - determinism_consensus_network.py: Consensus determinism
> - consensus_network_smoke.py: 4-node consensus
> - consensus_network_smoke_8nodes.py: 8-node consensus
> - run_full_simulation.py: Multi-block simulation
> - run_full_simulation_8nodes.py: 8-node multi-block
> - test_consensus_coverage.py: Byzantine scenarios
>
> **Tất cả test**: `python tests/run_all_tests.py` → ✅ PASSED

#### Q2: "Tại sao có smoke test? Tại sao 8 node?"
**Trả lời**:
> **Smoke test**: 
> - "Smoke test" = bài test nhẹ, nhanh để check basic functionality
> - Không phải exhaustive (không test tất cả edge case)
> - Kiểm tra happy path
>
> **Tại sao 8 node?**
> - Yêu cầu: "minimum eight nodes"
> - BFT thường chỉ cần 4 node (chịu 1 Byzantine)
> - 8 node để demonstrate scalability

#### Q3: "Test coverage có test cái gì về consensus?"
**Trả lời**:
> **test_consensus_coverage.py** tests:
> ```python
> 1. test_two_proposals_same_height_only_one_finalized():
>    - Proposer A gửi block_X
>    - Proposer B gửi block_Y
>    - Check: Tất cả node finalize cùng 1 block (safety)
>
> 2. test_invalid_signature_in_consensus_flow():
>    - Gửi vote với signature="bad"
>    - Check: Vote bị reject, không đạt quorum
>
> 3. test_transaction_replay():
>    - Gửi cùng transaction 2 lần (block khác)
>    - Check: Không gây vấn đề (depend on app)
> ```

---

## 🔥 PHẦN 4: CÂU HỎI KHÓBAIT & TRÁNH CÓT BẪNG

### 4.1 **Những Câu Hỏi "Tế Nhị"**

#### Q: "Nếu tất cả 4 node đều Byzantine thì sao?"
**Trả lời**:
> **BFT giả thuyết**:
> - Chịu được ≤ ⌊(n-1)/3⌋ Byzantine node
> - 4 node → chịu được 1 Byzantine
> - 4 node toàn Byzantine → không có honest node → không có đảm bảo
>
> **Lab**: Giả sử tất cả node là honest (không test Byzantine quorum)

#### Q: "Network delay 10 giây, liveness còn không?"
**Trả lời**:
> **Liveness**: "If delays are bounded, new blocks can finalize"
>
> **Requirement**: 
> - Nếu delay ≤ D (hữu hạn) → mỗi block sẽ finalize trong D*f(n) thời gian
>
> **Lab**: Giả sử delay không quá lớn, no timeout mechanism → simple 2-phase
>
> **Thực tế**: 
> - Cần timeout logic (nếu không finalize sau T → go to next round)
> - Lab không implement timeout → simplified

#### Q: "Có quá nhiều node Byzantine thì đồng thuận fail?"
**Trả lời**:
> **Đúng**. BFT consensus requirement: ≤ ⌊(n-1)/3⌋ Byzantine
> 
> **Ví dụ**:
> - 4 node, 2 Byzantine: threshold=3, nhưng 2 honest+1 Byzantine = 3 → attacker có thể finalize block sai ⚠️
> - 7 node, 2 Byzantine: threshold=5, 5 honest ≥ 5 → OK, có 2 dishonest ngồi chơi
>
> **Lab**: Assume all honest

---

### 4.2 **Những Điều Cần Tránh Nói**

❌ **KHÔNG NÊN NÓI**:
- "Determinism = random.seed() là enough" → **SAI**, cần canonical JSON + ordered execution
- "Threshold là 50%+1" → **SAI**, phải là 2/3+1
- "Block hash không cần include state_root" → **INCOMPLETE**, conceptually state_root should commit
- "Vote không cần verify" → **SAI**, cần verify signature + domain separation
- "Network delay không quan trọng" → **SAI**, là part của unreliable network requirement

✅ **NÊN NÓI**:
- "Determinism đạt bằng RNG seeding + canonical encoding + ordered execution"
- "Threshold là strict majority = (n*2)/3+1"
- "Block header commits state via state_root (Merkle hash)"
- "Vote phải verify signature với domain VOTE:chain_id để prevent reuse"
- "NetworkSimulator mô phỏng delay, drop, duplicate như real network"

---

## 📝 PHẦN 5: NHỮNG ĐẶC ĐIỂM NỔIBẬT CÓ NHỜ NHÂN

### 5.1 **Điểm Mạnh Cần Highlight**

**Nếu được hỏi: "Những điểm mạnh của implementation?"**

1. **NetworkSimulator rất chi tiết**
   - Delay + jitter + drop + duplicate
   - Backpressure (rate limiting)
   - Header → body ordering
   - Configuration từ file (reproducible)

2. **Determinism hoàn toàn**
   - Seed-based RNG
   - Canonical JSON encoding
   - Run 2x → logs identical, state_hash identical
   - Test coverage chứng minh

3. **Cryptography đúng**
   - Ed25519 ký
   - Domain separation (TX/HEADER/VOTE)
   - Canonical encoding

4. **Test coverage tốt**
   - 9 unit test
   - 5+ e2e test
   - Test determinism, safety, liveness scenarios

### 5.2 **Điểm Yếu Nên Biết Trả Lời**

**Nếu được hỏi: "Những giới hạn / điểm cần improve?"**

1. **Vote verification là mock** (_mock_verify_signature)
   - Hiện tại luôn return True
   - Nên implement thực dùng crypto layer
   - (OPTIONAL) Add pubkey_bytes vào Vote class

2. **Không có timeout logic**
   - Nếu proposal delay → không có next round
   - Liveness requirement: "if delays bounded" → cần timeout

3. **Owner check không enforce**
   - Requirement: "transaction affects data owned by sender"
   - Lab không validate sender sở hữu key (ví dụ Alice modify Bob/msg được)

4. **Không test Byzantine voting**
   - Nếu validator vote cho 2 block cùng height → không test
   - Current test: FirstSeenNode (chốt block đầu tự động)

---

## 🎤 PHẦN 6: MẪUTRẢ LỜI CHO CÁC CÂU HỎI THƯỜNG GẶP

### 6.1 **Introduce Project**
**Q**: "Giới thiệu ngắn gọn lab này"

**Mẫu trả lời** (30 giây):
> Lab 01 là xây dựng minimal Layer 1 blockchain. Hệ thống gồm 4 layer chính:
> 1. **Cryptography**: Ed25519 ký, SHA-256 hash, domain separation (TX/HEADER/VOTE)
> 2. **Network**: Mô phỏng mạng không tin cậy (delay, drop, duplicate), backpressure, header→body ordering
> 3. **Consensus**: 2-pha voting (Prevote→Precommit), threshold = 2/3+1 votes
> 4. **Execution**: Deterministic state machine, Merkle state root, xác minh transaction
>
> Mục tiêu: Tất cả honest node hội tụ cùng chuỗi block được finalize, bất kể network gặp vấn đề.

### 6.2 **Algorithm Flow**
**Q**: "Describe consensus flow"

**Mẫu trả lời** (1 phút):
> **Vòng Consensus**:
> 1. Proposer (round-robin) create block → broadcast header
> 2. Node nhận header → broadcast PREVOTE vote cho block
> 3. Node thấy ≥ 2/3+1 PREVOTE → broadcast PRECOMMIT vote
> 4. Node thấy ≥ 2/3+1 PRECOMMIT → **FINALIZE** block
> 5. Finalized block add vào ledger, height++
>
> **Threshold = (n*2)/3 + 1**:
> - 4 node: 3 votes
> - 7 node: 5 votes
> - Đảm bảo: ≥2 quorum không thể overlap (safety)

### 6.3 **Why 2-Phase?**
**Q**: "Tại sao cần 2 pha prevote/precommit?"

**Mẫu trả lời**:
> **Phase 1 (Prevote)**: "Tôi thấy block này valid"
> - Node nhận block → validate format, signature → broadcast prevote
> - Nếu ≥ 2/3+1 prevote → block được confirm là valid
>
> **Phase 2 (Precommit)**: "Tôi biết ≥2/3+1 node cũng confirm block → finalize"
> - Nếu ≥ 2/3+1 precommit → block final
>
> **Lợi ích**:
> - **Safety**: 2 phase → 2 opportunity agree → stronger commitment
> - **Liveness**: Có cơ hội chuyển sang next round nếu prevote không đạt

### 6.4 **Determinism**
**Q**: "Làm sao achieve determinism?"

**Mẫu trả lời**:
> **Ba yếu tố**:
> 1. **Fixed RNG**: `random.Random(seed=S)` → same random sequence
> 2. **Canonical JSON**: sort_keys=True, no spaces → same bytes cho same object
> 3. **Ordered execution**: Transaction apply đúng thứ tự block → same state
>
> **Verify**:
> ```
> Run 1: logs1, state_hash1 = run_sim(seed=12345)
> Run 2: logs2, state_hash2 = run_sim(seed=12345)
> assert logs1 == logs2 && state_hash1 == state_hash2
> ```
>
> **Test files**: determinism_check.py, determinism_consensus_network.py → PASSED ✓

### 6.5 **Domain Separation**
**Q**: "Domain separation có ý nghĩa gì?"

**Mẫu trả lời**:
> **Domain Separation** = Prefix riêng cho mỗi message type trước ký
>
> **Ví dụ**:
> - TX: "TX:chain_id|{...payload...}"
> - HEADER: "HEADER:chain_id|{...payload...}"
> - VOTE: "VOTE:chain_id|{...payload...}"
>
> **Tại sao?**
> - Nếu không có: Signature cho TX có thể reuse cho HEADER (DANGER!)
> - Có domain: Signature cho TX, validate fail cho HEADER (khác prefix → khác message)
> 
> **Security implication**: Prevent cross-context signature reuse

---

## 🎯 PHẦN 7: QUICK CHECKLIST TRƯỚC THI

### Pre-Exam Checklist (1 ngày trước)
- [ ] Đọc lại PHẦN 1 (4 khái niệm + 4 yếu tố)
- [ ] Học 6 class chính: ExecutionState, Transaction, NetworkSimulator, ConsensusEngine, Block, Ledger
- [ ] Nhớ threshold công thức: (n*2)/3+1
- [ ] Nhớ domain separation: TX, HEADER, VOTE prefixes
- [ ] Biết flow: Prevote → Precommit → Finalize
- [ ] Biết determinism yếu tố: RNG + canonical JSON + ordered execution

### During Exam
- [ ] **Nghe kỹ câu hỏi** trước khi trả lời
- [ ] **Trả lời từ từ**, không vội
- [ ] **Dùng ví dụ** (ví dụ 4 node, 7 node)
- [ ] **Nếu không biết**: Nói "Đó là phần tôi chưa fully implement" thay vì bịa
- [ ] **Nếu bị hỏi sâu**: Hỏi lại người hỏi để clarify

### Common Mistakes to Avoid
- ❌ Nói threshold là "50%+1" (sai, phải 2/3+1)
- ❌ Nói "determinism = random.seed() enough" (sai, cần canonical + ordered)
- ❌ Quên domain separation (TX vs HEADER signature reuse risk)
- ❌ Quên explain why 2 phases (lấy safety & liveness trade-off)
- ❌ Nói "vote không cần verify" (sai, cần verify đảm bảo authenticity)

---

## 📚 TÓMSẮT - NHỮNG ĐIỀU NHẤT ĐỊNH NHỚ

### **Top 5 Điều Nhất Định Nhớ**

| # | Điều | Ví Dụ / Công Thức |
|---|------|----------------|
| 1 | **Threshold** | (n*2)/3 + 1 → 4 node = 3, 7 node = 5 |
| 2 | **Domain Sep** | TX:chain_id, HEADER:chain_id, VOTE:chain_id |
| 3 | **Determinism** | Seed RNG + Canonical JSON + Ordered Execution |
| 4 | **Consensus Flow** | Propose → Prevote → Precommit → Finalize |
| 5 | **State Root** | Merkle tree over sorted (key, value) pairs |

### **Các Module/File Chính**
- **crypto/signing.py**: Ed25519 sign/verify
- **encoding/codec.py**: Canonical JSON, domain separation
- **execution/execution.py**: ExecutionState, state root
- **network/simulator.py**: Mạng với delay/drop/dup
- **consensus/engine.py**: Vote counting, threshold check
- **simulator/block.py, ledger.py**: Block structure, ledger

---

## 🚀 LỜI CUỐI

**Bí quyết trả lời tốt**:
1. ✅ Hiểu **tại sao** (why), không chỉ **làm sao** (how)
2. ✅ Dùng **ví dụ cụ thể** (4 node, 7 node, Alice, Bob)
3. ✅ Liên kết giữa các concept (determinism → canonical JSON; safety → threshold)
4. ✅ Nếu không biết: Nói thật thay vì bịa bromua

**Good luck với kỳ vấn đáp!** 🎓📚

---

*Document created: Jan 22, 2025*  
*For: Lab 01 Blockchain Viva Exam*
