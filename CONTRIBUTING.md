# Contributing

ขอบคุณที่สนใจร่วมพัฒนา parc-ferme!

## การเตรียม Development Environment

```bash
git clone https://github.com/passakorn/parc-ferme.git
cd parc-ferme
make dev
```

## การรันเทสต์

```bash
make test
```

## แนวทางการ Contribute

1. Fork repo แล้ว clone มาที่เครื่อง
2. สร้าง branch ใหม่จาก `main`: `git checkout -b feature/your-feature`
3. เขียนโค้ดและเทสต์ให้ครบ
4. รัน `make test` ให้ผ่านทั้งหมด
5. Commit ด้วย message ที่ชัดเจน
6. Push แล้วเปิด Pull Request

## Code Style

- ใช้ Python 3.10+ type hints
- ตั้งชื่อตัวแปรและฟังก์ชันเป็นภาษาอังกฤษ
- Docstring เป็นภาษาอังกฤษ

## การรายงาน Bug

เปิด Issue พร้อมข้อมูล:
- Python version
- OS
- ขั้นตอนในการ reproduce
- Error message / traceback

## License

การ contribute ถือว่ายอมรับ [MIT License](LICENSE) ของโปรเจกต์
